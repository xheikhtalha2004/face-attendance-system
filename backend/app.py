"""
Flask API Server for Face Attendance System
Implements REST API endpoints per SRDS specification
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sys
from datetime import datetime, timedelta
import cv2
import numpy as np
from dotenv import load_dotenv

# Add ml_cvs to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ml_cvs'))

from db import (
    db, init_db, User, Student, Attendance,
    get_all_students, get_student_by_id, create_student, update_student, delete_student,
    get_all_attendance, create_attendance, get_student_attendance_today,
    get_all_face_encodings, get_settings, update_setting
)
from recognition import recognize_from_frame, process_registration

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
CORS(app, origins=os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(','))
jwt = JWTManager(app)
init_db(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new admin user"""
    try:
        data = request.get_json()
        
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        if not all([email, password, name]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User already exists'}), 409
        
        # Create user
        password_hash = generate_password_hash(password)
        user = User(email=email, password_hash=password_hash, name=name)
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=email)
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict(),
            'access_token': access_token
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login and get JWT token"""
    try:
        data = request.get_json()
        
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({'error': 'Missing email or password'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create access token
        access_token = create_access_token(identity=email)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# STUDENT ENDPOINTS
# ============================================================================

@app.route('/api/students', methods=['GET'])
@jwt_required()
def get_students():
    """Get all students"""
    try:
        students = get_all_students()
        return jsonify([s.to_dict() for s in students]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/students/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student(student_id):
    """Get student by ID"""
    try:
        student = get_student_by_id(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        return jsonify(student.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/students', methods=['POST'])
@jwt_required()
def register_student():
    """Register new student with face image"""
    try:
        # Get form data
        name = request.form.get('name')
        student_id = request.form.get('studentId')
        department = request.form.get('department', 'General')
        email = request.form.get('email')
        
        if not all([name, student_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check for photo
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo provided'}), 400
        
        file = request.files['photo']
        
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save photo
        filename = secure_filename(f"{student_id}_{datetime.now().timestamp()}.jpg")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process image for face recognition
        image = cv2.imread(filepath)
        
        if image is None:
            os.remove(filepath)
            return jsonify({'error': 'Invalid image file'}), 400
        
        # Extract face embedding
        result = process_registration(image)
        
        if not result['success']:
            os.remove(filepath)
            return jsonify({'error': result['message']}), 400
        
        # Create student record
        student = create_student(
            name=name,
            student_id=student_id,
            department=department,
            email=email,
            photo_path=filename,
            face_encoding=result['embedding']
        )
        
        return jsonify({
            'message': 'Student registered successfully',
            'student': student.to_dict()
        }), 201
        
    except Exception as e:
        app.logger.error(f"Error registering student: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/students/<int:student_id>', methods=['PUT'])
@jwt_required()
def update_student_info(student_id):
    """Update student information"""
    try:
        data = request.get_json()
        
        student = update_student(student_id, **data)
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        return jsonify({
            'message': 'Student updated successfully',
            'student': student.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/students/<int:student_id>', methods=['DELETE'])
@jwt_required()
def delete_student_record(student_id):
    """Delete student"""
    try:
        success = delete_student(student_id)
        
        if not success:
            return jsonify({'error': 'Student not found'}), 404
        
        return jsonify({'message': 'Student deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ATTENDANCE ENDPOINTS
# ============================================================================

@app.route('/api/attendance', methods=['GET'])
@jwt_required()
def get_attendance_records():
    """Get attendance records with optional filters"""
    try:
        date_filter = request.args.get('date')
        student_id = request.args.get('studentId')
        
        records = get_all_attendance(
            date_filter=date_filter,
            student_id=int(student_id) if student_id else None
        )
        
        return jsonify([r.to_dict() for r in records]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/recognize', methods=['POST'])
@jwt_required()
def recognize_face():
    """Real-time face recognition from frame"""
    try:
        # Get frame from request
        if 'frame' not in request.files:
            return jsonify({'error': 'No frame provided'}), 400
        
        file = request.files['frame']
        
        # Read image
        file_bytes = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid image'}), 400
        
        # Get all known face encodings
        known_embeddings = get_all_face_encodings()
        
        if not known_embeddings:
            return jsonify({
                'recognized': False,
                'message': 'No enrolled students'
            }), 200
        
        # Get confidence threshold from settings
        settings = get_settings()
        threshold = float(settings.get('confidence_threshold', 0.6))
        
        # Recognize face
        result = recognize_from_frame(frame, known_embeddings, threshold=threshold)
        
        # If recognized, create attendance record
        if result['recognized']:
            student_id = result['student_id']
            
            # Check if already marked today
            existing_attendance = get_student_attendance_today(student_id)
            
            if not existing_attendance:
                # Determine status (Late/Present based on time)
                late_threshold = int(settings.get('late_threshold_minutes', 15))
                current_hour = datetime.now().hour
                current_minute = datetime.now().minute
                
                # Assume classes start at 9:00 AM
                is_late = (current_hour > 9) or (current_hour == 9 and current_minute > late_threshold)
                status = 'Late' if is_late else 'Present'
                
                # Create attendance
                attendance = create_attendance(
                    student_id=student_id,
                    status=status,
                    confidence=result['confidence'],
                    method='auto'
                )
                
                result['attendance_created'] = True
                result['attendance_id'] = attendance.id
                result['status'] = status
            else:
                result['attendance_created'] = False
                result['message'] = 'Already marked present today'
        
        return jsonify(result), 200
        
    except Exception as e:
        app.logger.error(f"Recognition error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/attendance/mark', methods=['POST'])
@jwt_required()
def mark_attendance_manual():
    """Manually mark attendance"""
    try:
        data = request.get_json()
        
        student_id = data.get('studentId')
        status = data.get('status', 'Present')
        notes = data.get('notes')
        
        if not student_id:
            return jsonify({'error': 'Student ID required'}), 400
        
        # Create attendance
        attendance = create_attendance(
            student_id=int(student_id),
            status=status,
            method='manual',
            notes=notes
        )
        
        return jsonify({
            'message': 'Attendance marked successfully',
            'attendance': attendance.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SETTINGS ENDPOINTS
# ============================================================================

@app.route('/api/settings', methods=['GET'])
@jwt_required()
def get_system_settings():
    """Get system settings"""
    try:
        settings = get_settings()
        return jsonify(settings), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings', methods=['PUT'])
@jwt_required()
def update_system_settings():
    """Update system settings"""
    try:
        data = request.get_json()
        
        for key, value in data.items():
            update_setting(key, str(value))
        
        return jsonify({'message': 'Settings updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# UPLOAD ENDPOINTS
# ============================================================================

@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           FaceAttend Pro - Backend Server                    ║
    ║                                                              ║
    ║   API running at: http://localhost:{port}                     ║
    ║   Database: {app.config['SQLALCHEMY_DATABASE_URI'][:30]}...  ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
