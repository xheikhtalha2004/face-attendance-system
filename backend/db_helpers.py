"""
CRUD helper functions for database models
Fixed to work around circular imports by importing inside functions
"""
from datetime import datetime, timedelta

# ============================================================================
# CRUD Operations for new models
# ============================================================================

# Course Management
def get_all_courses():
    """Get all courses"""
    from db import Course
    return Course.query.order_by(Course.course_id).all()


def get_course_by_id(course_id):
    """Get course by ID"""
    from db import Course
    return Course.query.get(course_id)


def get_course_by_course_id(course_id_str):
    """Get course by course_id string (e.g., 'CS101')"""
    from db import Course
    return Course.query.filter_by(course_id=course_id_str).first()


def create_course(course_id, course_name, professor_name=None, description=None):
    """Create new course"""
    from db import db, Course
    course = Course(
        course_id=course_id,
        course_name=course_name,
        professor_name=professor_name,
        description=description,
        is_active=True
    )
    db.session.add(course)
    db.session.commit()
    return course


def update_course(course_id, **kwargs):
    """Update course information"""
    from db import db, Course
    course = Course.query.get(course_id)
    if not course:
        return None
    
    for key, value in kwargs.items():
        if hasattr(course, key):
            setattr(course, key, value)
    
    course.updated_at = datetime.utcnow()
    db.session.commit()
    return course


def delete_course(course_id):
    """Delete course"""
    from db import db, Course
    course = Course.query.get(course_id)
    if course:
        db.session.delete(course)
        db.session.commit()
        return True
    return False


# TimeSlot Management
def get_all_time_slots():
    """Get all time slots ordered by day and slot number"""
    from db import db, TimeSlot
    return TimeSlot.query.order_by(
        db.case(
            (TimeSlot.day_of_week == 'MONDAY', 1),
            (TimeSlot.day_of_week == 'TUESDAY', 2),
            (TimeSlot.day_of_week == 'WEDNESDAY', 3),
            (TimeSlot.day_of_week == 'THURSDAY', 4),
            (TimeSlot.day_of_week == 'FRIDAY', 5),
        ),
        TimeSlot.slot_number
    ).all()


def get_time_slot_by_day_slot(day_of_week, slot_number):
    """Get time slot by day and slot number"""
    from db import TimeSlot
    return TimeSlot.query.filter_by(
        day_of_week=day_of_week,
        slot_number=slot_number
    ).first()


def create_or_update_time_slot(day_of_week, slot_number, course_id, start_time, end_time, 
                                late_threshold_minutes=5):
    """Create or update time slot"""
    from db import db, TimeSlot
    slot = get_time_slot_by_day_slot(day_of_week, slot_number)
    
    if slot:
        # Update existing
        slot.course_id = course_id
        slot.start_time = start_time
        slot.end_time = end_time
        slot.late_threshold_minutes = late_threshold_minutes
        slot.updated_at = datetime.utcnow()
    else:
        # Create new
        slot = TimeSlot(
            day_of_week=day_of_week,
            slot_number=slot_number,
            course_id=course_id,
            start_time=start_time,
            end_time=end_time,
            late_threshold_minutes=late_threshold_minutes,
            is_active=True
        )
        db.session.add(slot)
    
    db.session.commit()
    return slot


def delete_time_slot(slot_id):
    """Delete time slot"""
    from db import db, TimeSlot
    slot = TimeSlot.query.get(slot_id)
    if slot:
        db.session.delete(slot)
        db.session.commit()
        return True
    return False


def get_active_slots_for_day(day_of_week):
    """Get active time slots for a specific day"""
    from db import TimeSlot
    return TimeSlot.query.filter_by(
        day_of_week=day_of_week,
        is_active=True
    ).order_by(TimeSlot.slot_number).all()


# Session Management
def create_session(course_id, starts_at, ends_at, time_slot_id=None, 
                  late_threshold_minutes=5, auto_created=False, created_by=None):
    """Create new session"""
    from db import db, Session
    session = Session(
        course_id=course_id,
        time_slot_id=time_slot_id,
        starts_at=starts_at,
        ends_at=ends_at,
        late_threshold_minutes=late_threshold_minutes,
        status='ACTIVE',
        auto_created=auto_created,
        created_by_user_id=created_by
    )
    db.session.add(session)
    db.session.commit()
    return session


def get_session_by_id(session_id):
    """Get session by ID"""
    from db import Session
    return Session.query.get(session_id)


def get_active_session():
    """Get currently active session"""
    from db import Session
    return Session.query.filter_by(status='ACTIVE').first()


def get_sessions_by_date(date):
    """Get sessions for a specific date"""
    from db import Session
    start_of_day = datetime.combine(date, datetime.min.time())
    end_of_day = datetime.combine(date, datetime.max.time())
    
    return Session.query.filter(
        Session.starts_at >= start_of_day,
        Session.starts_at <= end_of_day
    ).order_by(Session.starts_at).all()


def update_session_status(session_id, status):
    """Update session status"""
    from db import db, Session
    session = Session.query.get(session_id)
    if session:
        session.status = status
        db.session.commit()
        return session
    return None


def get_attendance_by_session(session_id):
    """Get all attendance records for a session"""
    from db import Attendance
    return Attendance.query.filter_by(session_id=session_id).all()


# Student Embedding Management
def create_student_embedding(student_id, embedding, quality_score=None, sample_image_path=None):
    """Create new embedding entry for student"""
    from db import db, StudentEmbedding
    student_emb = StudentEmbedding(
        student_id=student_id,
        embedding=embedding,
        quality_score=quality_score,
        sample_image_path=sample_image_path
    )
    db.session.add(student_emb)
    db.session.commit()
    return student_emb


def get_student_all_embeddings(student_id):
    """Get all embeddings for a student"""
    from db import StudentEmbedding
    embeddings = StudentEmbedding.query.filter_by(student_id=student_id).all()
    return embeddings


def get_all_students_with_embeddings():
    """Get all students with their embeddings for recognition"""
    from db import Student
    students = Student.query.filter_by(status='Active').all()
    result = []
    
    for student in students:
        embeddings = get_student_all_embeddings(student.id)
        if embeddings:
            result.append({
                'student_id': student.id,
                'student_name': student.name,
                'embeddings': [emb.embedding for emb in embeddings]
            })
    
    return result


def delete_student_embedding(embedding_id):
    """Delete specific embedding"""
    from db import db, StudentEmbedding
    embedding = StudentEmbedding.query.get(embedding_id)
    if embedding:
        db.session.delete(embedding)
        db.session.commit()
        return True
    return False


# Updated Attendance Functions
def upsert_attendance(session_id, student_id, status='PRESENT', confidence=None, 
                     method='AUTO', notes=None, snapshot_path=None):
    """Create or update attendance record (upsert)"""
    from db import db, Attendance, Session
    
    # Check existing
    existing = Attendance.query.filter_by(
        session_id=session_id,
        student_id_fk=student_id
    ).first()
    
    if existing:
        # Update existing record
        existing.last_seen_time = datetime.utcnow()
        if confidence and confidence > (existing.confidence or 0):
            existing.confidence = confidence
        if notes:
            existing.notes = notes
        db.session.commit()
        return existing
    else:
        # Create new record
        session = Session.query.get(session_id)
        
        # Determine status based on time
        if status == 'PRESENT':
            late_cutoff = session.starts_at + timedelta(minutes=session.late_threshold_minutes)
            if datetime.utcnow() > late_cutoff:
                status = 'LATE'
        
        attendance = Attendance(
            session_id=session_id,
            student_id_fk=student_id,
            check_in_time=datetime.utcnow(),
            last_seen_time=datetime.utcnow(),
            status=status,
            confidence=confidence,
            method=method,
            notes=notes,
            snapshot_path=snapshot_path
        )
        db.session.add(attendance)
        db.session.commit()
        return attendance


def mark_students_absent(session_id, student_ids):
    """Mark multiple students as absent for a session"""
    from db import db, Attendance, Session
    session = Session.query.get(session_id)
    if not session:
        return []
    
    marked = []
    for student_id in student_ids:
        # Check if not already marked
        existing = Attendance.query.filter_by(
            session_id=session_id,
            student_id_fk=student_id
        ).first()
        
        if not existing:
            attendance = Attendance(
                session_id=session_id,
                student_id_fk=student_id,
                check_in_time=None,
                last_seen_time=None,
                status='ABSENT',
                method='AUTO',
                notes='Auto-marked absent (not detected during session)'
            )
            db.session.add(attendance)
            marked.append(attendance)
    
    db.session.commit()
    return marked
