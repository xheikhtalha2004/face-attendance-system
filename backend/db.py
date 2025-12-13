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
    
    # Relationship
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    
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
    """Attendance records model"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id_fk = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default='Present')  # Present, Late, Absent
    confidence = db.Column(db.Float)
    method = db.Column(db.String(50), default='auto')  # auto (face recognition) or manual
    notes = db.Column(db.Text)
    
    def to_dict(self):
        student = Student.query.get(self.student_id_fk)
        return {
            'id': str(self.id),
            'studentId': str(self.student_id_fk),
            'studentName': student.name if student else 'Unknown',
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'confidence': round(self.confidence, 2) if self.confidence else 0,
            'method': self.method,
            'notes': self.notes
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
        print("✓ Database initialized successfully")


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
