"""
Flask API Server for Face Attendance System
Implements REST API endpoints per SRDS specification
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
import logging
from datetime import datetime, timedelta
import cv2
import numpy as np
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

# Add ml_cvs to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ml_cvs'))

from db import (
    db, init_db, Student, Attendance,
    get_all_students, get_student_by_id, create_student, update_student, delete_student,
    get_all_attendance, create_attendance, get_student_attendance_today,
    get_all_face_encodings, get_settings, update_setting, get_student_by_student_id
)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
CORS(app, origins=['*'], supports_credentials=True, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], allow_headers=['Content-Type', 'Authorization'])

# Add CORS headers manually as fallback
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response
init_db(app)

# Register blueprints
from timetable_api import timetable_bp
app.register_blueprint(timetable_bp)

from registration_api import registration_bp
app.register_blueprint(registration_bp)

from enrollment_api import enrollment_bp
app.register_blueprint(enrollment_bp)

from student_management_api import student_mgmt_bp
app.register_blueprint(student_mgmt_bp)

from session_management_api import session_mgmt_bp
app.register_blueprint(session_mgmt_bp)

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
# STUDENT ENDPOINTS
# ============================================================================

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get all students"""
    try:
        students = get_all_students()
        return jsonify([s.to_dict() for s in students]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/students/<int:student_id>', methods=['GET'])
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

        # Prevent duplicate roll numbers before any processing
        if get_student_by_student_id(student_id):
            return jsonify({'error': f'Student ID {student_id} already exists'}), 409
        
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
        
    except IntegrityError as ie:
        db.session.rollback()
        app.logger.error(f"Constraint violation during registration: {str(ie)}")
        return jsonify({'error': 'Student already exists or data constraint failed'}), 409
    except Exception as e:
        app.logger.error(f"Error registering student: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/students/<int:student_id>/enroll-frames', methods=['POST'])
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
def delete_student_record(student_id):
    """Delete student"""
    try:
        from db import Attendance

        if Attendance.query.filter_by(student_id_fk=student_id).first():
            return jsonify({'error': 'Cannot delete student with existing attendance records'}), 409

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
def recognize_face():
    """
    Real-time face recognition (single-pass, threshold-based) with re-entry detection
    """
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Decode base64 image
        import base64
        img_data = data['image'].split(',')[1] if ',' in data['image'] else data['image']
        img_bytes = base64.b64decode(img_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Get active session (auto-closes expired ones)
        from db import get_active_session
        active_session = get_active_session()
        
        if not active_session:
            return jsonify({'recognized': False, 'message': 'No active session'}), 200
        
        # Initialize face engine (lazy loading)
        global _face_engine
        if _face_engine is None:
            try:
                from ml_cvs.face_engine import create_face_engine
                _face_engine = create_face_engine(use_gpu=False)
                app.logger.info("Face engine initialized")
            except ImportError as e:
                app.logger.error(f"InsightFace not installed: {str(e)}")
                return jsonify({
                    'recognized': False,
                    'error': 'InsightFace not installed. See INSIGHTFACE_INSTALL.md for instructions.'
                }), 500
            except Exception as e:
                app.logger.error(f"Face engine initialization error: {str(e)}")
                return jsonify({
                    'recognized': False,
                    'error': f'Face engine error: {str(e)}'
                }), 500
        
        # Detect faces
        faces = _face_engine.detect_faces(frame)
        
        if len(faces) == 0:
            return jsonify({'recognized': False, 'message': 'No face detected'}), 200
        
        if len(faces) > 1:
            return jsonify({
                'recognized': False, 
                'message': f'Multiple faces detected ({len(faces)}). Please ensure only one person in frame'
            }), 200
        
        # Extract embedding
        query_embedding = faces[0]['embedding']
        
        # Load ALL registered students (not just enrolled ones)
        # This allows us to detect intruders (registered but not enrolled)
        from db import Enrollment, Student, db
        import pickle
        from db import get_student_all_embeddings
        
        all_students = Student.query.filter(Student.deleted_at.is_(None)).all()
        
        if not all_students:
            return jsonify({
                'recognized': False, 
                'message': 'No students registered in system'
            }), 200
        
        # Get embeddings for ALL students
        student_data = []
        for student in all_students:
            embeddings = get_student_all_embeddings(student.id)
            if embeddings:
                student_data.append((
                    student.id,
                    student.name,
                    [pickle.loads(emb.embedding) for emb in embeddings]
                ))
        
        if not student_data:
            return jsonify({
                'recognized': False, 
                'message': 'No facial data available for any registered students'
            }), 200
        
        # Use single-pass matching with a 0.60 similarity threshold
        confidence_threshold = float(get_settings().get('confidence_threshold', '0.6'))
        match = _face_engine.find_best_match(query_embedding, student_data, threshold=confidence_threshold)
        
        if not match:
            return jsonify({
                'recognized': False, 
                'message': 'Unknown face (not enrolled in this course or below confidence threshold)',
                'confidenceThreshold': confidence_threshold
            }), 200
        
        sid, student_name, similarity = match

        # Check enrollment
        enrollment = Enrollment.query.filter_by(
            student_id=sid,
            course_id=active_session.course_id
        ).first()
        
        # Check if already marked (whether enrolled or intruder)
        from db import Attendance, ReEntryLog
        existing = Attendance.query.filter_by(
            session_id=active_session.id,
            student_id_fk=sid
        ).first()
        
        if existing:
            # RE-ENTRY DETECTION
            out_log = ReEntryLog(
                session_id=active_session.id,
                student_id=sid,
                action='OUT',
                is_suspicious=True
            )
            db.session.add(out_log)
            
            in_log = ReEntryLog(
                session_id=active_session.id,
                student_id=sid,
                action='IN',
                is_suspicious=True
            )
            db.session.add(in_log)
            db.session.commit()
            
            app.logger.warning(f"Re-entry detected: {student_name} (ID: {sid}) in session {active_session.id}")
            
            return jsonify({
                'recognized': True,
                'alreadyMarked': True,
                'reEntry': True,
                'studentId': sid,
                'studentName': student_name,
                'confidence': round(similarity, 3),
                'message': 'Re-entry detected! Logged as suspicious.',
                'attendance': existing.to_dict()
            }), 200
        
        # Determine status based on enrollment
        if not enrollment:
            # NOT ENROLLED - Mark as INTRUDER
            from db import upsert_attendance
            attendance = upsert_attendance(
                session_id=active_session.id,
                student_id=sid,
                status='INTRUDER',
                confidence=similarity,
                method='AUTO'
            )
            
            intruder_log = ReEntryLog(
                session_id=active_session.id,
                student_id=sid,
                action='INTRUDER',
                is_suspicious=True
            )
            db.session.add(intruder_log)
            db.session.commit()
            
            app.logger.warning(f"⚠️ INTRUDER DETECTED: {student_name} (ID: {sid}) not enrolled in course {active_session.course_id}")
            
            return jsonify({
                'recognized': True,
                'intruder': True,
                'studentId': sid,
                'studentName': student_name,
                'confidence': round(similarity, 3),
                'message': f'⚠️ INTRUDER ALERT: {student_name} is not enrolled in this course!',
                'attendance': attendance.to_dict()
            }), 200
        
        # ENROLLED - Mark as PRESENT or LATE
        from db import upsert_attendance
        attendance = upsert_attendance(
            session_id=active_session.id,
            student_id=sid,
            status='PRESENT',  # Will auto-detect LATE based on time
            confidence=similarity,
            method='AUTO'
        )
        
        entry_log = ReEntryLog(
            session_id=active_session.id,
            student_id=sid,
            action='IN',
            is_suspicious=False
        )
        db.session.add(entry_log)
        db.session.commit()
        
        app.logger.info(f"Attendance marked: {student_name} (ID: {sid}) - {attendance.status} (confidence {round(similarity,3)})")
        
        return jsonify({
            'recognized': True,
            'studentId': sid,
            'studentName': student_name,
            'confidence': round(similarity, 3),
            'message': f'Attendance marked: {attendance.status}',
            'attendance': attendance.to_dict(),
            'session': active_session.to_dict()
        }), 200
        
    except Exception as e:
        app.logger.error(f'Recognition error: {str(e)}')
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/test-recognition', methods=['POST'])
def test_face_recognition():
    """
    Test face recognition against all students without session requirements.
    Provides detailed debugging information about detection, matching, and similarity scores.
    Uses YuNet detector + InsightFace embeddings (512D ArcFace).
    """
    try:
        data = request.get_json()

        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        # Decode base64 image
        import base64
        img_data = data['image'].split(',')[1] if ',' in data['image'] else data['image']
        img_bytes = base64.b64decode(img_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({'error': 'Invalid image data'}), 400

        # Initialize FaceEngine (uses InsightFace for embeddings, consistent with enrollment)
        from ml_cvs.face_engine import FaceEngine
        import pickle
        face_engine = FaceEngine()

        # Step 1: Detect faces
        detection_start = datetime.now()
        detected_faces = face_engine.detect_faces(frame)
        detection_time = (datetime.now() - detection_start).total_seconds() * 1000

        detection_info = {
            'faces_detected': len(detected_faces),
            'detection_time_ms': round(detection_time, 2),
            'faces': []
        }

        if len(detected_faces) == 0:
            return jsonify({
                'success': False,
                'message': 'No faces detected in image',
                'detection': detection_info,
                'embedding': None,
                'matching': None
            }), 200

        if len(detected_faces) > 1:
            detection_info['warning'] = f'Multiple faces detected ({len(detected_faces)}), using first face'

        # Use first detected face
        face_data = detected_faces[0]
        bbox = face_data['bbox']
        query_embedding = face_data['embedding']  # InsightFace embedding (512D)
        
        detection_info['faces'].append({
            'x': int(bbox[0]),
            'y': int(bbox[1]),
            'width': int(bbox[2] - bbox[0]),
            'height': int(bbox[3] - bbox[1])
        })

        embedding_info = {
            'extraction_time_ms': round(detection_time, 2),  # Included in detection time
            'embedding_shape': query_embedding.shape if hasattr(query_embedding, 'shape') else len(query_embedding)
        }

        # Step 2: Get all students with embeddings
        from db_helpers import get_all_students_with_embeddings
        students_data = get_all_students_with_embeddings()

        if not students_data:
            return jsonify({
                'success': False,
                'message': 'No students with embeddings found in database',
                'detection': detection_info,
                'embedding': embedding_info,
                'matching': None
            }), 200

        # Step 3: Compare against all students
        matching_start = datetime.now()
        matching_results = []

        for student in students_data:
            student_id = student['student_id']
            student_name = student['student_name']
            student_embeddings = student['embeddings']

            # Calculate similarities for all embeddings of this student
            similarities = []
            distances = []
            for emb_bytes in student_embeddings:
                try:
                    known_embedding = pickle.loads(emb_bytes)  # Deserialize InsightFace embedding
                    if known_embedding is not None:
                        # Calculate cosine similarity (both embeddings should be 512D)
                        similarity = face_engine.compare_embeddings_cosine(query_embedding, known_embedding)
                        similarities.append(round(float(similarity), 4))
                        # Use distance for additional info (1 - cosine_similarity)
                        distances.append(round(float(1.0 - similarity), 4))
                    else:
                        similarities.append(0.0)
                        distances.append(1.0)
                except Exception as e:
                    app.logger.warning(f"Error calculating similarity for student {student_id}: {str(e)}")
                    similarities.append(0.0)
                    distances.append(1.0)

            # Use best similarity for this student
            best_similarity = max(similarities) if similarities else 0.0
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
            best_distance = min(distances) if distances else 1.0

            matching_results.append({
                'student_id': student_id,
                'student_name': student_name,
                'similarities': similarities,
                'distances': distances,
                'best_similarity': round(best_similarity, 4),
                'avg_similarity': round(avg_similarity, 4),
                'best_distance': round(best_distance, 4) if best_distance != 1.0 else None,
                'embedding_count': len(student_embeddings)
            })

        matching_time = (datetime.now() - matching_start).total_seconds() * 1000

        # Sort by best similarity (descending)
        matching_results.sort(key=lambda x: x['best_similarity'], reverse=True)

        # Find best match
        best_match = matching_results[0] if matching_results else None

        matching_info = {
            'total_students_tested': len(matching_results),
            'matching_time_ms': round(matching_time, 2),
            'results': matching_results,
            'best_match': best_match
        }

        # Determine recognition result
        confidence_threshold = float(get_settings().get('confidence_threshold', '0.6'))

        recognition_result = {
            'recognized': best_match and best_match['best_similarity'] >= confidence_threshold,
            'student_id': best_match['student_id'] if best_match else None,
            'student_name': best_match['student_name'] if best_match else None,
            'confidence': best_match['best_similarity'] if best_match else 0.0,
            'threshold_used': confidence_threshold
        }

        return jsonify({
            'success': True,
            'message': 'Face recognition test completed',
            'recognition': recognition_result,
            'detection': detection_info,
            'embedding': embedding_info,
            'matching': matching_info
        }), 200

    except Exception as e:
        app.logger.error(f'Test recognition error: {str(e)}')
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# Global instances for face engine and stabilizer
_face_engine = None


@app.route('/api/attendance/mark', methods=['POST'])
def mark_attendance_manual():
    """Manually mark attendance"""
    try:
        data = request.get_json()
        
        student_id = data.get('studentId')
        session_id = data.get('sessionId')
        status = data.get('status', 'PRESENT')
        notes = data.get('notes')
        
        if not student_id or not session_id:
            return jsonify({'error': 'studentId and sessionId are required'}), 400

        from db import Session, Student, Enrollment, upsert_attendance

        session = Session.query.get(int(session_id))
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        if session.status != 'ACTIVE':
            return jsonify({'error': 'Session is not active'}), 409

        student = Student.query.get(int(student_id))
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Ensure student is enrolled in the course for the session
        enrollment = Enrollment.query.filter_by(
            student_id=student.id,
            course_id=session.course_id
        ).first()
        if not enrollment:
            return jsonify({'error': 'Student is not enrolled in this course'}), 409

        normalized_status = status.upper()
        if normalized_status not in ['PRESENT', 'LATE', 'ABSENT']:
            return jsonify({'error': 'Invalid status. Use PRESENT, LATE, or ABSENT'}), 400

        attendance = upsert_attendance(
            session_id=session.id,
            student_id=student.id,
            status=normalized_status,
            method='MANUAL',
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


@app.route('/api/sessions/<int:session_id>/finalize', methods=['POST'])
def finalize_session(session_id):
    """
    Manually finalize session and mark absentees
    Only marks absent students who are enrolled in the course
    """
    try:
        from db import Session, Enrollment, Attendance, Student, db, mark_students_absent
        
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session.status == 'COMPLETED':
            return jsonify({'error': 'Session already finalized'}), 400
        
        # Get enrolled students for this course
        enrolled = db.session.query(Student.id).join(Enrollment).filter(
            Enrollment.course_id == session.course_id
        ).all()
        enrolled_ids = [e[0] for e in enrolled]
        
        # Get students with attendance
        present = db.session.query(Attendance.student_id_fk).filter_by(
            session_id=session_id
        ).all()
        present_ids = set([p[0] for p in present])
        
        # Mark absentees (enrolled but not present)
        absent_ids = [sid for sid in enrolled_ids if sid not in present_ids]
        marked = mark_students_absent(session_id, absent_ids)
        
        # Update session status
        session.status = 'COMPLETED'
        db.session.commit()
        
        app.logger.info(f"Session {session_id} finalized. {len(marked)} students marked absent.")
        
        return jsonify({
            'message': f'Session finalized. {len(marked)} students marked absent.',
            'absentCount': len(marked),
            'totalEnrolled': len(enrolled_ids),
            'presentCount': len(present_ids),
            'session': session.to_dict()
        }), 200
        
    except Exception as e:
        app.logger.error(f"Finalization error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<int:session_id>/export', methods=['GET'])
def export_session_csv_endpoint(session_id):
    """Export session attendance as CSV file"""
    try:
        from flask import Response
        from export_service import export_session_csv
        
        csv_data = export_session_csv(session_id)
        
        if csv_data is None:
            return jsonify({'error': 'Session not found'}), 404
        
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=session_{session_id}_attendance.csv'}
        )
    except Exception as e:
        app.logger.error(f"Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.route('/api/dashboard/stats', methods=['GET'])
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
def get_system_settings():
    """Get system settings"""
    try:
        settings = get_settings()
        return jsonify(settings), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings', methods=['PUT'])
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
