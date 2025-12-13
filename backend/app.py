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

# Register blueprints
from timetable_api import timetable_bp
app.register_blueprint(timetable_bp)

# Initialize scheduler service for auto-session creation
from scheduler_service import init_scheduler
scheduler = init_scheduler(app)

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
        
        # Extract face embedding using new system
        from enrollment_service import process_single_registration_image
        result = process_single_registration_image(image)
        
        if not result['success']:
            os.remove(filepath)
            return jsonify({'error': result['message']}), 400
        
        # Create student record (keep face_encoding for backwards compatibility)
        student = create_student(
            name=name,
            student_id=student_id,
            department=department,
            email=email,
            photo_path=filename,
            face_encoding=result['embedding']
        )
        
        # Also create first StudentEmbedding entry
        from db import create_student_embedding
        create_student_embedding(
            student_id=student.id,
            embedding=result['embedding'],
            quality_score=0.8  # Estimated for single image
        )
        
        return jsonify({
            'message': 'Student registered successfully',
            'student': student.to_dict()
        }), 201
        
    except Exception as e:
        app.logger.error(f"Error registering student: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/students/<int:student_id>/enroll-frames', methods=['POST'])
@jwt_required()
def enroll_student_multi_frame(student_id):
    """
    Enhanced enrollment with multiple frames
    Accepts 10-20 frames from webcam, extracts best quality embeddings
    """
    try:
        data = request.get_json()
        
        frames_b64 = data.get('frames', [])
        max_embeddings = data.get('maxEmbeddings', 10)
        
        if not frames_b64:
            return jsonify({'error': 'No frames provided'}), 400
        
        # Process frames
        from enrollment_service import process_enrollment_frames
        result = process_enrollment_frames(frames_b64, max_embeddings=max_embeddings)
        
        if not result['success']:
            return jsonify({'error': result['message']}), 400
        
        # Get student
        student = get_student_by_id(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Delete old embeddings for this student
        from db import StudentEmbedding, db
        StudentEmbedding.query.filter_by(student_id=student_id).delete()
        db.session.commit()
        
        # Save new embeddings
        from db import create_student_embedding
        for idx, (embedding_bytes, quality_score) in enumerate(zip(result['embeddings'], result['quality_scores'])):
            create_student_embedding(
                student_id=student_id,
                embedding=embedding_bytes,
                quality_score=quality_score
            )
        
        # Update student's legacy face_encoding with best embedding
        student.face_encoding = result['embeddings'][0]
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': result['message'],
            'embeddingsSaved': len(result['embeddings']),
            'totalFrames': result['total_frames'],
            'validFrames': result['valid_frames']
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in multi-frame enrollment: {str(e)}")
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
    """
    Enhanced face recognition with InsightFace + K-of-N stabilization
    Returns recognition result and updates session attendance if confirmed
    """
    try:
        # Get frame from request
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Decode base64 image
        from enrollment_service import decode_base64_image
        frame = decode_base64_image(data['image'])
        
        if frame is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Initialize face engine and stabilizer (singleton pattern recommended in production)
        from ml_cvs.face_engine import create_face_engine
        from ml_cvs.stabilizer import RecognitionStabilizer
        import sys
        
        # Create or get global instances
        if not hasattr(app, 'face_engine'):
            app.face_engine = create_face_engine(use_gpu=False)
            app.logger.info("Face engine initialized")
        
        if not hasattr(app, 'stabilizer'):
            app.stabilizer = RecognitionStabilizer(k=5, n=10, cooldown_seconds=120)
            app.logger.info("Stabilizer initialized")
        
        face_engine = app.face_engine
        stabilizer = app.stabilizer
        
        # Detect faces in frame
        detected_faces = face_engine.detect_faces(frame)
        
        if not detected_faces:
            return jsonify({
                'recognized': False,
                'message': 'No face detected',
                'progress': {}
            }), 200
        
        if len(detected_faces) > 1:
            return jsonify({
                'recognized': False,
                'message': f'Multiple faces detected ({len(detected_faces)}). Please ensure only one person in frame',
                'faceCount': len(detected_faces)
            }), 200
        
        # Get the single detected face
        face_data = detected_faces[0]
        query_embedding = face_data['embedding']
        landmarks = face_data['kps']
        det_score = face_data['det_score']
        
        # Quality check
        from ml_cvs.quality import check_quality_gates
        from ml_cvs.face_engine import extract_crop_from_bbox
        
        face_crop = extract_crop_from_bbox(frame, face_data['bbox'])
        quality = check_quality_gates(face_crop, landmarks)
        
        if not quality['passed']:
            return jsonify({
                'recognized': False,
                'message': f'Quality check failed: {quality["reason"]}',
                'quality': quality
            }), 200
        
        # Get all students with embeddings
        from db import get_all_students_with_embeddings
        students_data = get_all_students_with_embeddings()
        
        if not students_data:
            return jsonify({
                'recognized': False,
                'message': 'No enrolled students found'
            }), 200
        
        # Prepare for matching: format as (student_id, student_name, [embeddings])
        import pickle
        known_embeddings = []
        for student_data in students_data:
            student_id = student_data['student_id']
            student_name = student_data['student_name']
            embeddings_serialized = student_data['embeddings']
            
            # Deserialize embeddings
            embeddings = [pickle.loads(emb_bytes) for emb_bytes in embeddings_serialized]
            known_embeddings.append((student_id, student_name, embeddings))
        
        # Find best match
        match_result = face_engine.find_best_match(
            query_embedding,
            known_embeddings,
            threshold=0.35
        )
        
        if match_result is None:
            # No match - update stabilizer with None
            stabilizer.update(None, 0.0)
            
            return jsonify({
                'recognized': False,
                'message': 'Face not recognized',
                'confidence': 0.0
            }), 200
        
        student_id, student_name, similarity = match_result
        
        # Update stabilizer
        stabilizer.update(student_id, similarity)
        
        # Check if confirmed (K-of-N threshold met)
        confirmed = stabilizer.get_confirmed()
        
        if confirmed:
            confirmed_student_id, confirmed_similarity = confirmed
            
            # Mark as confirmed to start cooldown
            stabilizer.mark_confirmed(confirmed_student_id)
            
            # Get active session
            from db import get_active_session, upsert_attendance
            active_session = get_active_session()
            
            if not active_session:
                return jsonify({
                    'recognized': True,
                    'confirmed': True,
                    'studentId': confirmed_student_id,
                    'studentName': student_name,
                    'confidence': round(confirmed_similarity, 3),
                    'message': 'Confirmed! But no active session to mark attendance',
                    'session': None
                }), 200
            
            # Upsert attendance (creates or updates)
            attendance = upsert_attendance(
                session_id=active_session.id,
                student_id=confirmed_student_id,
                status='PRESENT',  # Will be adjusted by upsert logic
                confidence=confirmed_similarity,
                method='AUTO',
                notes=f'Confirmed with {similarity:.3f} similarity (K-of-N voting)'
            )
            
            # Get progress for UI
            progress = stabilizer.get_progress(confirmed_student_id)
            
            return jsonify({
                'recognized': True,
                'confirmed': True,
                'studentId': confirmed_student_id,
                'studentName': student_name,
                'confidence': round(confirmed_similarity, 3),
                'message': f'Attendance marked: {attendance.status}',
                'session': {
                    'id': active_session.id,
                    'courseName': active_session.course.course_name if active_session.course else None,
                    'professorName': active_session.course.professor_name if active_session.course else None
                },
                'attendance': attendance.to_dict(),
                'progress': progress
            }), 200
        
        else:
            # Not confirmed yet - show progress
            progress = stabilizer.get_progress(student_id)
            
            return jsonify({
                'recognized': True,
                'confirmed': False,
                'verifying': True,
                'studentId': student_id,
                'studentName': student_name,
                'confidence': round(similarity, 3),
                'message': f'Verifying... ({progress["matched"]}/{progress["required"]})',
                'progress': progress
            }), 200
        
    except Exception as e:
        app.logger.error(f"Recognition error: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
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
# SESSION ENDPOINTS
# ============================================================================

@app.route('/api/sessions/active', methods=['GET'])
@jwt_required()
def get_active_session_endpoint():
    """Get currently active session"""
    try:
        from db import get_active_session
        session = get_active_session()
        
        if not session:
            return jsonify({
                'active': False,
                'session': None,
                'message': 'No active session found'
            }), 200
        
        return jsonify({
            'active': True,
            'session': session.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/today', methods=['GET'])
@jwt_required()
def get_today_sessions():
    """Get all sessions for today"""
    try:
        from db import get_sessions_by_date
        from datetime import date
        
        today = date.today()
        sessions = get_sessions_by_date(today)
        
        return jsonify([s.to_dict() for s in sessions]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics for today"""
    try:
        from datetime import date, datetime
        
        # Get today's stats
        today = date.today()
        
        # Total students
        total_students = Student.query.filter_by(status='Active').count()
        
        # Today's attendance
        today_attendance = Attendance.query.filter(
            db.func.date(Attendance.check_in_time) == today
        ).all()
        
        present_count = sum(1 for a in today_attendance if a.status in ['PRESENT', 'LATE'])
        late_count = sum(1 for a in today_attendance if a.status == 'LATE')
        
        # Attendance rate
        attendance_rate = (present_count / total_students * 100) if total_students > 0 else 0
        
        # Get active session
        from db import get_active_session
        active_session = get_active_session()
        
        return jsonify({
            'totalStudents': total_students,
            'presentToday': present_count,
            'lateArrivals': late_count,
            'attendanceRate': round(attendance_rate, 1),
            'activeSession': active_session.to_dict() if active_session else None,
            'lastUpdated': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        app.logger.error(f"Dashboard stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/weekly', methods=['GET'])
@jwt_required()
def get_weekly_attendance():
    """Get weekly attendance data for charts"""
    try:
        from datetime import date, timedelta
        
        # Get last 7 days
        today = date.today()
        weekly_data = []
        
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            
            day_attendance = Attendance.query.filter(
                db.func.date(Attendance.check_in_time) == day
            ).all()
            
            present = sum(1 for a in day_attendance if a.status in ['PRESENT', 'LATE'])
            absent = sum(1 for a in day_attendance if a.status == 'ABSENT')
            
            weekly_data.append({
                'name': day.strftime('%a'),  # Mon, Tue, etc.
                'date': day.isoformat(),
                'present': present,
                'absent': absent
            })
        
        return jsonify(weekly_data), 200
        
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

    print(
        "------------------------------------------------------------\n"
        "  FaceAttend Pro - Backend Server\n"
        f"  API running at: http://localhost:{port}\n"
        f"  Database: {app.config['SQLALCHEMY_DATABASE_URI'][:30]}...\n"
        "------------------------------------------------------------"
    )

    app.run(host='0.0.0.0', port=port, debug=debug)

