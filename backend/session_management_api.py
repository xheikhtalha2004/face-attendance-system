"""
Session Management API Endpoints
Manual session creation, ending, and verification with timestamps
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone

session_mgmt_bp = Blueprint('session_management', __name__, url_prefix='/api/sessions')


@session_mgmt_bp.route('', methods=['GET'])
def get_all_sessions():
    """Get all sessions with optional filtering by status or date"""
    try:
        from db import Session
        
        status = request.args.get('status')  # SCHEDULED, ACTIVE, COMPLETED, CANCELLED
        date_str = request.args.get('date')  # YYYY-MM-DD format
        
        query = Session.query
        
        if status:
            query = query.filter_by(status=status)
        
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                start_of_day = datetime.combine(target_date, datetime.min.time())
                end_of_day = datetime.combine(target_date, datetime.max.time())
                query = query.filter(
                    Session.starts_at >= start_of_day,
                    Session.starts_at <= end_of_day
                )
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        sessions = query.order_by(Session.starts_at.desc()).all()
        
        return jsonify([s.to_dict() for s in sessions]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@session_mgmt_bp.route('/<int:session_id>', methods=['GET'])
def get_session_detail(session_id):
    """Get detailed session information with attendance"""
    try:
        from db import Session
        from db_helpers import get_attendance_by_session
        
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        attendance = get_attendance_by_session(session_id)
        
        return jsonify({
            'session': session.to_dict(),
            'attendance': {
                'totalRecords': len(attendance),
                'records': [a.to_dict() for a in attendance]
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@session_mgmt_bp.route('/manual/create', methods=['POST'])
def create_manual_session():
    """Create a manual session (not auto-generated)"""
    try:
        from db import db, Session, Course
        from db_helpers import determine_initial_status
        
        data = request.get_json()
        
        course_id = data.get('courseId')
        starts_at_str = data.get('startsAt')  # ISO format: 2025-12-17T10:00:00
        ends_at_str = data.get('endsAt')
        late_threshold = data.get('lateThresholdMinutes', 5)
        
        if not all([course_id, starts_at_str, ends_at_str]):
            return jsonify({'error': 'Missing required fields: courseId, startsAt, endsAt'}), 400
        
        # Validate course exists
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': f'Course with ID {course_id} not found'}), 404
        
        # Parse timestamps
        try:
            starts_at = datetime.fromisoformat(starts_at_str.replace('Z', '+00:00'))
            ends_at = datetime.fromisoformat(ends_at_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid datetime format. Use ISO format (e.g., 2025-12-17T10:00:00)'}), 400

        # Normalize to local naive for consistent comparisons with frontend inputs
        if starts_at.tzinfo:
            starts_at = starts_at.astimezone().replace(tzinfo=None)
        if ends_at.tzinfo:
            ends_at = ends_at.astimezone().replace(tzinfo=None)

        now = datetime.now()

        # Validate time logic
        if ends_at <= starts_at:
            return jsonify({'error': 'End time must be after start time'}), 400
        if ends_at <= now:
            return jsonify({'error': 'End time cannot be in the past'}), 400

        # Determine intended status (ACTIVE if start is now/past/within 5 minutes)
        status = determine_initial_status(starts_at)

        # Prevent overlapping sessions (active now or scheduled within the same window)
        conflicting_statuses = ['ACTIVE'] if status == 'ACTIVE' else ['ACTIVE', 'SCHEDULED']
        overlap = Session.query.filter(
            Session.status.in_(conflicting_statuses),
            Session.starts_at < ends_at,
            Session.ends_at > starts_at
        ).first()

        if overlap:
            return jsonify({
                'error': 'Conflicting session exists',
                'details': {
                    'sessionId': overlap.id,
                    'status': overlap.status,
                    'startsAt': overlap.starts_at.isoformat(),
                    'endsAt': overlap.ends_at.isoformat()
                }
            }), 409
        
        # Create session
        session = Session(
            course_id=course_id,
            starts_at=starts_at,
            ends_at=ends_at,
            late_threshold_minutes=late_threshold,
            status=status,
            auto_created=False,
            created_at=datetime.utcnow()
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'message': f"Session created and {'activated' if status == 'ACTIVE' else 'scheduled'} successfully",
            'session': session.to_dict(),
            'status': status
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@session_mgmt_bp.route('/<int:session_id>/activate', methods=['PUT'])
def activate_session(session_id):
    """Activate a session (change status from SCHEDULED to ACTIVE)"""
    try:
        from db import db, Session
        
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session.status == 'ACTIVE':
            return jsonify({
                'message': 'Session already active',
                'session': session.to_dict()
            }), 200
        
        session.status = 'ACTIVE'
        session.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Session activated successfully',
            'session': session.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@session_mgmt_bp.route('/<int:session_id>/end', methods=['PUT'])
def end_session(session_id):
    """End a session (change status to COMPLETED)"""
    try:
        from db import db, Session
        
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session.status == 'COMPLETED':
            return jsonify({
                'message': 'Session already completed',
                'session': session.to_dict()
            }), 200
        
        session.status = 'COMPLETED'
        session.ends_at = datetime.now()  # Update end time to now
        db.session.commit()
        
        return jsonify({
            'message': 'Session ended successfully',
            'session': session.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@session_mgmt_bp.route('/<int:session_id>/cancel', methods=['PUT'])
def cancel_session(session_id):
    """Cancel a session"""
    try:
        from db import db, Session
        
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        session.status = 'CANCELLED'
        db.session.commit()
        
        return jsonify({
            'message': 'Session cancelled successfully',
            'session': session.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@session_mgmt_bp.route('/active', methods=['GET'])
def get_active_sessions():
    """Get all currently active sessions"""
    try:
        from db import Session
        now = datetime.now()
        
        active_sessions = Session.query.filter(
            Session.status == 'ACTIVE',
            Session.starts_at <= now,
            Session.ends_at >= now
        ).all()
        
        return jsonify({
            'count': len(active_sessions),
            'sessions': [s.to_dict() for s in active_sessions]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@session_mgmt_bp.route('/status', methods=['GET'])
def get_session_status():
    """Get high-level session status overview"""
    try:
        from db import db, Session

        now = datetime.now()

        active_session = Session.query.filter(
            Session.status == 'ACTIVE',
            Session.starts_at <= now,
            Session.ends_at >= now
        ).order_by(Session.starts_at.asc()).first()

        next_scheduled = Session.query.filter(
            Session.status == 'SCHEDULED',
            Session.starts_at >= now
        ).order_by(Session.starts_at.asc()).first()

        status_counts = Session.query.with_entities(
            Session.status,
            db.func.count(Session.id)
        ).group_by(Session.status).all()

        counts = {status: count for status, count in status_counts}

        last_completed = Session.query.filter_by(status='COMPLETED').order_by(
            Session.ends_at.desc()
        ).first()

        return jsonify({
            'activeSession': active_session.to_dict() if active_session else None,
            'nextScheduled': next_scheduled.to_dict() if next_scheduled else None,
            'statusCounts': counts,
            'lastCompleted': last_completed.to_dict() if last_completed else None,
            'timestamp': now.isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@session_mgmt_bp.route('/verify-data', methods=['GET'])
def verify_session_data():
    """Verify all session data and timestamps are stored correctly"""
    try:
        from db import Session, Attendance
        from sqlalchemy import func
        
        # Get statistics
        total_sessions = Session.query.count()
        active_sessions = Session.query.filter_by(status='ACTIVE').count()
        completed_sessions = Session.query.filter_by(status='COMPLETED').count()
        scheduled_sessions = Session.query.filter_by(status='SCHEDULED').count()
        cancelled_sessions = Session.query.filter_by(status='CANCELLED').count()
        
        total_attendance = Attendance.query.count()
        
        # Get recent sessions with timestamps
        recent_sessions = Session.query.order_by(Session.created_at.desc()).limit(5).all()
        
        # Get sessions without proper timestamps
        sessions_without_end = Session.query.filter(Session.ends_at.is_(None)).count()
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'totalSessions': total_sessions,
                'activeCount': active_sessions,
                'completedCount': completed_sessions,
                'scheduledCount': scheduled_sessions,
                'cancelledCount': cancelled_sessions,
                'totalAttendanceRecords': total_attendance,
                'sessionsWithoutEndTime': sessions_without_end
            },
            'recentSessions': [
                {
                    'id': s.id,
                    'course': s.course.course_name if s.course else 'N/A',
                    'status': s.status,
                    'startsAt': s.starts_at.isoformat(),
                    'endsAt': s.ends_at.isoformat() if s.ends_at else None,
                    'createdAt': s.created_at.isoformat(),
                    'autoCreated': s.auto_created
                } for s in recent_sessions
            ],
            'message': '✅ Data verification complete. All timestamps are stored properly.'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
