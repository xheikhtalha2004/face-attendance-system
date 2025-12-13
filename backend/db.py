"""
Database models and operations for Face Attendance System
Uses SQLAlchemy ORM for database management
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class User(db.Model):
    """Admin user model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }


class Student(db.Model):
    """Student model with face embeddings"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(db.String(100))
    email = db.Column(db.String(120))
    photo_path = db.Column(db.String(255))
    face_encoding = db.Column(db.LargeBinary)  # Store face encoding as BLOB
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    embeddings = db.relationship('StudentEmbedding', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'studentId': self.student_id,
            'department': self.department or 'General',
            'email': self.email,
            'photoUrl': f'/api/uploads/{self.photo_path}' if self.photo_path else None,
            'status': self.status,
            'createdAt': self.created_at.isoformat(),
            'hasEmbedding': self.face_encoding is not None
        }


class Attendance(db.Model):
    """Attendance records model - session-based with unique constraint"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=True)  # Nullable for migration
    student_id_fk = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_seen_time = db.Column(db.DateTime)  # For continuous tracking
    status = db.Column(db.String(20), default='PRESENT')  # PRESENT, LATE, ABSENT
    confidence = db.Column(db.Float)  # Similarity/distance score
    method = db.Column(db.String(50), default='AUTO')  # AUTO (face recognition) or MANUAL
    notes = db.Column(db.Text)
    snapshot_path = db.Column(db.String(255))  # Optional snapshot of detected face
    
    # Unique constraint: one attendance record per student per session
    __table_args__ = (
        db.UniqueConstraint('session_id', 'student_id_fk', name='uq_session_student'),
    )
    
    def to_dict(self):
        student = Student.query.get(self.student_id_fk)
        session = Session.query.get(self.session_id) if self.session_id else None
        
        return {
            'id': str(self.id),
            'sessionId': self.session_id,
            'studentId': str(self.student_id_fk),
            'studentName': student.name if student else 'Unknown',
            'checkInTime': self.check_in_time.isoformat() if self.check_in_time else None,
            'lastSeenTime': self.last_seen_time.isoformat() if self.last_seen_time else None,
            'status': self.status,
            'confidence': round(self.confidence, 2) if self.confidence else 0,
            'method': self.method,
            'notes': self.notes,
            'snapshotPath': self.snapshot_path,
            # Include session info if available
            'courseName': session.course.course_name if session and session.course else None,
            'professorName': session.course.professor_name if session and session.course else None
        }



class Settings(db.Model):
    """System settings model"""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value,
            'updatedAt': self.updated_at.isoformat()
        }


class Course(db.Model):
    """Course master data"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String(50), unique=True, nullable=False)  # e.g., "CS101"
    course_name = db.Column(db.String(200), nullable=False)
    professor_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    time_slots = db.relationship('TimeSlot', backref='course', lazy=True, cascade='all, delete-orphan')
    sessions = db.relationship('Session', backref='course', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'courseId': self.course_id,
            'courseName': self.course_name,
            'professorName': self.professor_name,
            'description': self.description,
            'isActive': self.is_active,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }


class TimeSlot(db.Model):
    """Weekly timetable slots"""
    __tablename__ = 'time_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(10), nullable=False)  # MONDAY, TUESDAY, etc.
    slot_number = db.Column(db.Integer, nullable=False)  # 1-5
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)  # "08:30"
    end_time = db.Column(db.String(5), nullable=False)    # "09:50"
    late_threshold_minutes = db.Column(db.Integer, default=5)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one course per day/slot combination
    __table_args__ = (
        db.UniqueConstraint('day_of_week', 'slot_number', name='uq_day_slot'),
    )
    
    # Relationships
    sessions = db.relationship('Session', backref='time_slot', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'dayOfWeek': self.day_of_week,
            'slotNumber': self.slot_number,
            'courseId': self.course_id,
            'courseName': self.course.course_name if self.course else None,
            'professorName': self.course.professor_name if self.course else None,
            'startTime': self.start_time,
            'endTime': self.end_time,
            'lateThresholdMinutes': self.late_threshold_minutes,
            'isActive': self.is_active
        }


class Session(db.Model):
    """Class sessions (auto-generated or manual)"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.id'), nullable=True)  # Nullable for manual sessions
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)
    late_threshold_minutes = db.Column(db.Integer, default=5)
    status = db.Column(db.String(20), default='ACTIVE')  # SCHEDULED, ACTIVE, COMPLETED, CANCELLED
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    auto_created = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'courseId': self.course_id,
            'courseName': self.course.course_name if self.course else None,
            'professorName': self.course.professor_name if self.course else None,
            'timeSlotId': self.time_slot_id,
            'startsAt': self.starts_at.isoformat(),
            'endsAt': self.ends_at.isoformat(),
            'lateThresholdMinutes': self.late_threshold_minutes,
            'status': self.status,
            'autoCreated': self.auto_created,
            'createdAt': self.created_at.isoformat()
        }


class StudentEmbedding(db.Model):
    """Multiple face embeddings per student for better accuracy"""
    __tablename__ = 'student_embeddings'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    embedding = db.Column(db.LargeBinary, nullable=False)  # Serialized numpy array
    quality_score = db.Column(db.Float)  # Quality metric for this sample
    sample_image_path = db.Column(db.String(255))  # Optional reference image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'studentId': self.student_id,
            'qualityScore': self.quality_score,
            'sampleImagePath': self.sample_image_path,
            'createdAt': self.created_at.isoformat()
        }



def init_db(app):
    """Initialize database"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Create default settings if not exist
        default_settings = {
            'confidence_threshold': '0.6',
            'late_threshold_minutes': '15',
            'camera_device_id': '',
            'min_face_size': '20'
        }
        
        for key, value in default_settings.items():
            if not Settings.query.filter_by(key=key).first():
                setting = Settings(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
        print("Database initialized successfully")


# CRUD Operations

def get_all_students():
    """Get all students"""
    return Student.query.order_by(Student.created_at.desc()).all()


def get_student_by_id(student_id):
    """Get student by ID"""
    return Student.query.get(student_id)


def get_student_by_student_id(student_id_str):
    """Get student by student ID string"""
    return Student.query.filter_by(student_id=student_id_str).first()


def create_student(name, student_id, department=None, email=None, photo_path=None, face_encoding=None):
    """Create new student"""
    student = Student(
        name=name,
        student_id=student_id,
        department=department,
        email=email,
        photo_path=photo_path,
        face_encoding=face_encoding,
        status='Active'
    )
    db.session.add(student)
    db.session.commit()
    return student


def update_student(student_id, **kwargs):
    """Update student information"""
    student = Student.query.get(student_id)
    if not student:
        return None
    
    for key, value in kwargs.items():
        if hasattr(student, key):
            setattr(student, key, value)
    
    student.updated_at = datetime.utcnow()
    db.session.commit()
    return student


def delete_student(student_id):
    """Delete student"""
    student = Student.query.get(student_id)
    if student:
        db.session.delete(student)
        db.session.commit()
        return True
    return False


def get_all_attendance(date_filter=None, student_id=None):
    """Get attendance records with optional filters"""
    query = Attendance.query
    
    if date_filter:
        # Filter by date
        query = query.filter(db.func.date(Attendance.timestamp) == date_filter)
    
    if student_id:
        query = query.filter_by(student_id_fk=student_id)
    
    return query.order_by(Attendance.timestamp.desc()).all()


def create_attendance(student_id, status='Present', confidence=None, method='auto', notes=None):
    """Create attendance record"""
    attendance = Attendance(
        student_id_fk=student_id,
        status=status,
        confidence=confidence,
        method=method,
        notes=notes
    )
    db.session.add(attendance)
    db.session.commit()
    return attendance


def get_attendance_today():
    """Get today's attendance"""
    today = datetime.utcnow().date()
    return Attendance.query.filter(db.func.date(Attendance.timestamp) == today).all()


def get_student_attendance_today(student_id):
    """Check if student has attendance record today"""
    today = datetime.utcnow().date()
    return Attendance.query.filter(
        db.func.date(Attendance.timestamp) == today,
        Attendance.student_id_fk == student_id
    ).first()


def get_all_face_encodings():
    """Get all students with face encodings for recognition"""
    students = Student.query.filter(Student.face_encoding.isnot(None), Student.status == 'Active').all()
    return [(student.id, student.name, student.face_encoding) for student in students]


def get_settings():
    """Get all settings as dictionary"""
    settings = Settings.query.all()
    return {s.key: s.value for s in settings}


def update_setting(key, value):
    """Update or create setting"""
    setting = Settings.query.filter_by(key=key).first()
    if setting:
        setting.value = value
        setting.updated_at = datetime.utcnow()
    else:
        setting = Settings(key=key, value=value)
        db.session.add(setting)
    
    db.session.commit()
    return setting


# Import helper functions from sibling module (works when running from backend/)
from db_helpers import (
    # Course management
    get_all_courses, get_course_by_id, get_course_by_course_id,
    create_course, update_course, delete_course,
    # TimeSlot management  
    get_all_time_slots, get_time_slot_by_day_slot,
    create_or_update_time_slot, delete_time_slot, get_active_slots_for_day,
    # Session management
    create_session, get_session_by_id, get_active_session,
    get_sessions_by_date, update_session_status, get_attendance_by_session,
    # StudentEmbedding management
    create_student_embedding, get_student_all_embeddings,
    get_all_students_with_embeddings, delete_student_embedding,
    # Updated attendance functions
    upsert_attendance, mark_students_absent
)
