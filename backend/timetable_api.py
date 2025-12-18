"""
Session and Timetable Management API Endpoints
Handles course management, timetable scheduling, and session creation
"""
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, timedelta
import pandas as pd
import io

# Import DB functions
from db import (
    # Course management
    get_all_courses, get_course_by_id, create_course, update_course, delete_course,
    # TimeSlot management
    get_all_time_slots, get_time_slot_by_day_slot, create_or_update_time_slot, delete_time_slot,
    get_active_slots_for_day,
    # Session management
    create_session, get_session_by_id, get_active_session, get_sessions_by_date,
    update_session_status, get_attendance_by_session,
    # Attendance
    upsert_attendance, mark_students_absent,
    # Students
    get_all_students
)

# Create blueprint
timetable_bp = Blueprint('timetable', __name__, url_prefix='/api')


def _parse_time_str(value):
    """Validate and parse HH:MM values"""
    try:
        return datetime.strptime(value, '%H:%M').time()
    except Exception:
        return None


# ============================================================================
# COURSE ENDPOINTS
# ============================================================================

@timetable_bp.route('/courses', methods=['GET'])
def get_courses():
    """Get all courses"""
    try:
        courses = get_all_courses()
        return jsonify([c.to_dict() for c in courses]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/courses', methods=['POST'])
def create_course_endpoint():
    """Create new course"""
    try:
        data = request.get_json()

        course_id = data.get('courseId')
        course_name = data.get('courseName')
        professor_name = data.get('professorName')
        description = data.get('description')

        if not all([course_id, course_name]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Prevent duplicate course codes
        from db_helpers import get_course_by_course_id
        if get_course_by_course_id(course_id):
            return jsonify({'error': f'Course {course_id} already exists'}), 409

        course = create_course(
            course_id=course_id,
            course_name=course_name,
            professor_name=professor_name,
            description=description
        )

        return jsonify({
            'message': 'Course created successfully',
            'course': course.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/courses/<int:course_id>', methods=['PUT'])
def update_course_endpoint(course_id):
    """Update course"""
    try:
        data = request.get_json()
        
        course = update_course(course_id, **data)
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        return jsonify({
            'message': 'Course updated successfully',
            'course': course.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/courses/<int:course_id>', methods=['DELETE'])
def delete_course_endpoint(course_id):
    """Delete course"""
    try:
        from db import Enrollment, Session as SessionModel

        if Enrollment.query.filter_by(course_id=course_id).first():
            return jsonify({'error': 'Cannot delete course with enrolled students'}), 409

        active_or_scheduled = SessionModel.query.filter(
            SessionModel.course_id == course_id,
            SessionModel.status.in_(['ACTIVE', 'SCHEDULED'])
        ).first()
        if active_or_scheduled:
            return jsonify({'error': 'Cannot delete course with active or scheduled sessions'}), 409

        success = delete_course(course_id)
        
        if not success:
            return jsonify({'error': 'Course not found'}), 404
        
        return jsonify({'message': 'Course deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# TIMETABLE/TIME SLOT ENDPOINTS
# ============================================================================

@timetable_bp.route('/timetable', methods=['GET'])
def get_timetable():
    """Get entire weekly timetable"""
    try:
        slots = get_all_time_slots()
        
        # Organize by day and slot number
        timetable = {
            'MONDAY': {},
            'TUESDAY': {},
            'WEDNESDAY': {},
            'THURSDAY': {},
            'FRIDAY': {}
        }
        
        for slot in slots:
            day = slot.day_of_week
            slot_num = str(slot.slot_number)
            timetable[day][slot_num] = slot.to_dict()
        
        return jsonify(timetable), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/timetable/slots', methods=['POST'])
def create_update_time_slot():
    """Create or update time slot"""
    try:
        data = request.get_json()
        
        day_of_week = data.get('dayOfWeek')
        slot_number = data.get('slotNumber')
        course_id = data.get('courseId')
        start_time = data.get('startTime')
        end_time = data.get('endTime')
        late_threshold_minutes = data.get('lateThresholdMinutes', 5)
        
        print(f'DEBUG: Received slot data: day={day_of_week}, slot={slot_number}, course_id={course_id}')
        
        if not all([day_of_week, slot_number, course_id, start_time, end_time]):
            return jsonify({'error': 'Missing required fields'}), 400

        start_time_obj = _parse_time_str(start_time)
        end_time_obj = _parse_time_str(end_time)
        if not start_time_obj or not end_time_obj:
            return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
        if end_time_obj <= start_time_obj:
            return jsonify({'error': 'End time must be after start time'}), 400
        
        # Validate that course exists
        from db_helpers import get_course_by_id
        course = get_course_by_id(course_id)
        print(f'DEBUG: Looking up course {course_id}: {course}')
        if not course:
            return jsonify({'error': f'Course with ID {course_id} not found'}), 404

        # Check for overlapping slots on the same day (excluding current slot if updating)
        from db import TimeSlot
        existing_slot = get_time_slot_by_day_slot(day_of_week, slot_number)
        existing_id = existing_slot.id if existing_slot else None

        day_slots = TimeSlot.query.filter(
            TimeSlot.day_of_week == day_of_week,
            TimeSlot.id != existing_id
        ).all()

        for other in day_slots:
            other_start = _parse_time_str(other.start_time)
            other_end = _parse_time_str(other.end_time)
            if other_start and other_end and start_time_obj < other_end and end_time_obj > other_start:
                return jsonify({
                    'error': 'Time slot overlaps with another slot on this day',
                    'conflictSlotId': other.id
                }), 409
        
        slot = create_or_update_time_slot(
            day_of_week=day_of_week,
            slot_number=slot_number,
            course_id=course_id,
            start_time=start_time,
            end_time=end_time,
            late_threshold_minutes=late_threshold_minutes
        )
        
        print(f'DEBUG: Slot saved successfully: {slot.to_dict()}')
        
        return jsonify({
            'message': 'Time slot saved successfully',
            'slot': slot.to_dict()
        }), 200
        
    except Exception as e:
        import traceback
        print(f'ERROR in create_update_time_slot: {str(e)}')
        print(traceback.format_exc())
        from app import app as flask_app
        flask_app.logger.error(f'Slot creation error: {str(e)}')
        flask_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@timetable_bp.route('/timetable/slots/<int:slot_id>', methods=['DELETE'])
def delete_time_slot_endpoint(slot_id):
    """Delete time slot"""
    try:
        from db import Session as SessionModel, TimeSlot

        slot = TimeSlot.query.get(slot_id)
        if not slot:
            return jsonify({'error': 'Time slot not found'}), 404

        active_session = SessionModel.query.filter_by(time_slot_id=slot_id).first()
        if active_session:
            return jsonify({'error': 'Cannot delete time slot with existing sessions'}), 409

        success = delete_time_slot(slot_id)
        
        if not success:
            return jsonify({'error': 'Time slot not found'}), 404
        
        return jsonify({'message': 'Time slot deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SESSION ENDPOINTS
# ============================================================================

@timetable_bp.route('/sessions', methods=['POST'])
def create_session_endpoint():
    """Create new session (manual)"""
    try:
        data = request.get_json()

        course_id = data.get('courseId')
        try:
            starts_at = datetime.fromisoformat(data.get('startsAt'))
            ends_at = datetime.fromisoformat(data.get('endsAt'))
        except Exception:
            return jsonify({'error': 'Invalid datetime format. Use ISO 8601 (e.g., 2025-12-17T10:00:00)'}), 400

        if starts_at.tzinfo:
            starts_at = starts_at.replace(tzinfo=None)
        if ends_at.tzinfo:
            ends_at = ends_at.replace(tzinfo=None)

        late_threshold_minutes = data.get('lateThresholdMinutes', 5)

        if not all([course_id, starts_at, ends_at]):
            return jsonify({'error': 'Missing required fields'}), 400

        if ends_at <= starts_at:
            return jsonify({'error': 'End time must be after start time'}), 400

        if ends_at <= datetime.utcnow():
            return jsonify({'error': 'End time cannot be in the past'}), 400

        # Prevent overlapping active sessions
        from db import Session as SessionModel
        conflict = SessionModel.query.filter(
            SessionModel.status == 'ACTIVE',
            SessionModel.starts_at < ends_at,
            SessionModel.ends_at > starts_at
        ).first()
        if conflict:
            return jsonify({
                'error': 'Another active session overlaps with this time window',
                'conflictSessionId': conflict.id
            }), 409

        from db_helpers import determine_initial_status
        initial_status = determine_initial_status(starts_at)

        session = create_session(
            course_id=course_id,
            starts_at=starts_at,
            ends_at=ends_at,
            late_threshold_minutes=late_threshold_minutes,
            auto_created=False,
            created_by=None,
            status=initial_status
        )
        
        return jsonify({
            'message': f"Session {'activated' if initial_status == 'ACTIVE' else 'scheduled'} successfully",
            'session': session.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details"""
    try:
        session = get_session_by_id(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify(session.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """Get all sessions with optional date filter"""
    try:
        date_filter = request.args.get('date')
        if date_filter:
            sessions = get_sessions_by_date(datetime.fromisoformat(date_filter))
        else:
            # Get all sessions (you might want to limit this in production)
            from db import Session
            sessions = Session.query.order_by(Session.starts_at.desc()).limit(100).all()

        return jsonify([s.to_dict() for s in sessions]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/sessions/active', methods=['GET'])
def get_active_session_endpoint():
    """Get currently active session"""
    try:
        session = get_active_session()

        if not session:
            return jsonify({'active': False}), 200

        return jsonify({
            'active': True,
            'session': session.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/sessions/<int:session_id>/attendance', methods=['GET'])
def get_session_attendance(session_id):
    """Get all attendance records for a session"""
    try:
        records = get_attendance_by_session(session_id)
        
        return jsonify([r.to_dict() for r in records]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/sessions/<int:session_id>/status', methods=['PUT'])
def update_session_status_endpoint(session_id):
    """Update session status"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if not status:
            return jsonify({'error': 'Status required'}), 400
        
        session = update_session_status(session_id, status)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'message': 'Session status updated',
            'session': session.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/sessions/<int:session_id>/mark-absentees', methods=['POST'])
def mark_absentees_endpoint(session_id):
    """Mark all students without attendance as absent"""
    try:
        session = get_session_by_id(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        # Get all active students
        all_students = get_all_students()
        all_student_ids = [s.id for s in all_students if s.status == 'Active']

        # Get students already marked
        attendance_records = get_attendance_by_session(session_id)
        marked_student_ids = set(a.student_id_fk for a in attendance_records)

        # Find absent students
        absent_student_ids = [sid for sid in all_student_ids if sid not in marked_student_ids]

        # Mark them absent
        marked = mark_students_absent(session_id, absent_student_ids)

        return jsonify({
            'message': f'Marked {len(marked)} students as absent',
            'count': len(marked)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/sessions/<int:session_id>/export', methods=['GET'])
def export_session_attendance(session_id):
    """Export session attendance to CSV or Excel"""
    try:
        format_type = request.args.get('format', 'csv').lower()
        if format_type not in ['csv', 'excel']:
            return jsonify({'error': 'Invalid format. Use csv or excel'}), 400

        session = get_session_by_id(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        attendance_records = get_attendance_by_session(session_id)

        # Prepare data for export
        data = []
        for record in attendance_records:
            student = record.student
            data.append({
                'Student Name': student.name if student else 'Unknown',
                'Roll Number': student.student_id if student else 'Unknown',
                'Attendance Status': record.status,
                'Check-in Time': record.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if record.check_in_time else 'N/A',
                'Last Seen Time': record.last_seen_time.strftime('%Y-%m-%d %H:%M:%S') if record.last_seen_time else 'N/A',
                'Confidence': f"{record.confidence:.2f}" if record.confidence else 'N/A',
                'Course Name': session.course.course_name if session.course else 'Unknown',
                'Professor Name': session.course.professor_name if session.course else 'Unknown',
                'Session Date': session.starts_at.strftime('%Y-%m-%d'),
                'Session Time': f"{session.starts_at.strftime('%H:%M')} - {session.ends_at.strftime('%H:%M')}"
            })

        if not data:
            return jsonify({'error': 'No attendance records found for this session'}), 404

        df = pd.DataFrame(data)

        # Create file in memory
        output = io.BytesIO()

        if format_type == 'csv':
            df.to_csv(output, index=False)
            output.seek(0)
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'attendance_session_{session_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        else:  # excel
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Attendance', index=False)
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'attendance_session_{session_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )

    except Exception as e:
        return jsonify({'error': str(e)}), 500
