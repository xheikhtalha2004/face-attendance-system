"""
Session and Timetable Management API Endpoints
Handles course management, timetable scheduling, and session creation
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta

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


# ============================================================================
# COURSE ENDPOINTS
# ============================================================================

@timetable_bp.route('/courses', methods=['GET'])
@jwt_required()
def get_courses():
    """Get all courses"""
    try:
        courses = get_all_courses()
        return jsonify([c.to_dict() for c in courses]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/courses', methods=['POST'])
@jwt_required()
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
@jwt_required()
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
@jwt_required()
def delete_course_endpoint(course_id):
    """Delete course"""
    try:
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
@jwt_required()
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
@jwt_required()
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
        
        if not all([day_of_week, slot_number, course_id, start_time, end_time]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        slot = create_or_update_time_slot(
            day_of_week=day_of_week,
            slot_number=slot_number,
            course_id=course_id,
            start_time=start_time,
            end_time=end_time,
            late_threshold_minutes=late_threshold_minutes
        )
        
        return jsonify({
            'message': 'Time slot saved successfully',
            'slot': slot.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/timetable/slots/<int:slot_id>', methods=['DELETE'])
@jwt_required()
def delete_time_slot_endpoint(slot_id):
    """Delete time slot"""
    try:
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
@jwt_required()
def create_session_endpoint():
    """Create new session (manual)"""
    try:
        from flask_jwt_extended import get_jwt_identity
        
        data = request.get_json()
        
        course_id = data.get('courseId')
        starts_at = datetime.fromisoformat(data.get('startsAt'))
        ends_at = datetime.fromisoformat(data.get('endsAt'))
        late_threshold_minutes = data.get('lateThresholdMinutes', 5)
        
        if not all([course_id, starts_at, ends_at]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get current user ID
        current_user_email = get_jwt_identity()
        from db import User
        user = User.query.filter_by(email=current_user_email).first()
        
        session = create_session(
            course_id=course_id,
            starts_at=starts_at,
            ends_at=ends_at,
            late_threshold_minutes=late_threshold_minutes,
            auto_created=False,
            created_by=user.id if user else None
        )
        
        return jsonify({
            'message': 'Session created successfully',
            'session': session.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id):
    """Get session details"""
    try:
        session = get_session_by_id(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify(session.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/sessions/active', methods=['GET'])
@jwt_required()
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
@jwt_required()
def get_session_attendance(session_id):
    """Get all attendance records for a session"""
    try:
        records = get_attendance_by_session(session_id)
        
        return jsonify([r.to_dict() for r in records]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/sessions/<int:session_id>/status', methods=['PUT'])
@jwt_required()
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
@jwt_required()
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
