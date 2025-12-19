"""
Student Self-Registration API
Allows students to register themselves with facial enrollment and course selection
"""
from flask import Blueprint, request, jsonify
import re

registration_bp = Blueprint('registration', __name__)

def validate_student_id(student_id):
    """Validate SPXX-BCS-XXX format"""
    pattern = r'^SP\d{2}-BCS-\d{3}$'
    return re.match(pattern, student_id) is not None

@registration_bp.route('/api/register/student', methods=['POST'])
def self_register():
    """
    Student self-registration with facial enrollment
    Request JSON:
    {
        "name": "Alice Smith",
        "studentId": "SP21-BCS-001",
        "email": "alice@test.com",
        "department": "Software Engineering",
        "frames": [...],  # 15 base64 frames
        "selectedCourses": [1, 2]  # Course IDs
    }
    """
    try:
        from app import app

        data = request.get_json()

        name = data.get('name')
        student_id = data.get('studentId')
        email = data.get('email')
        phone = data.get('phone')
        department = data.get('department') or 'General'
        frames = data.get('frames', [])
        selected_courses = data.get('selectedCourses', [])

        # Validation
        if not all([name, student_id]):
            return jsonify({'error': 'Name and Student ID are required'}), 400

        if not department:
            return jsonify({'error': 'Department is required'}), 400

        if not validate_student_id(student_id):
            return jsonify({'error': 'Invalid Student ID format. Use SPXX-BCS-XXX (e.g., SP21-BCS-001)'}), 400

        if not frames or len(frames) < 5:
            return jsonify({'error': 'At least 5 facial frames are required for enrollment'}), 400

        # Clean selected course IDs (deduplicate + ensure ints)
        try:
            selected_courses = list({int(c) for c in selected_courses})
        except Exception:
            return jsonify({'error': 'Course IDs must be numeric'}), 400

        # Check if student ID already exists
        from db import get_student_by_student_id
        if get_student_by_student_id(student_id):
            return jsonify({'error': f'Student ID {student_id} is already registered'}), 400

        # Process facial enrollment - REQUIRED for face recognition to work
        face_data_available = False
        result = None
        
        try:
            from enrollment_service import process_enrollment_frames
            app.logger.info(f"Processing {len(frames)} frames for student {student_id}")
            
            result = process_enrollment_frames(frames, max_embeddings=10)
            
            if result['success']:
                face_data_available = True
                app.logger.info(f"Face processing successful: {len(result['embeddings'])} embeddings extracted")
            else:
                # Face processing failed - return error instead of continuing
                error_msg = result.get('message', 'Unknown face processing error')
                app.logger.error(f"Face processing failed for {student_id}: {error_msg}")
                app.logger.error(f"Frames submitted: {result.get('total_frames', 0)}, Valid frames: {result.get('valid_frames', 0)}")
                return jsonify({
                    'error': f'Face enrollment failed: {error_msg}',
                    'details': {
                        'totalFrames': result.get('total_frames', 0),
                        'validFrames': result.get('valid_frames', 0),
                        'reason': error_msg
                    }
                }), 400
                
        except ImportError as e:
            app.logger.error(f"Face engine not available: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
            return jsonify({
                'error': 'Face recognition system not available. Please contact administrator.',
                'details': 'InsightFace or ML dependencies not installed'
            }), 500
            
        except Exception as e:
            app.logger.error(f"Face processing error for {student_id}: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
            return jsonify({
                'error': f'Face processing failed: {str(e)}',
                'details': 'Unexpected error during face enrollment'
            }), 500

        # Create student record (only if face processing succeeded)
        from db import create_student, create_student_embedding, db, Enrollment
        student = create_student(
            name=name,
            student_id=student_id,
            department=department,
            email=email,
            phone=phone,
            face_encoding=result['embeddings'][0]
        )

        # Save all embeddings
        embeddings_saved = 0
        for emb, quality in zip(result['embeddings'], result['quality_scores']):
            create_student_embedding(
                student_id=student.id,
                embedding=emb,
                quality_score=quality
            )
            embeddings_saved += 1
        
        app.logger.info(f"Saved {embeddings_saved} embeddings for student {student_id}")

        # Verify embeddings were saved
        from db import get_student_all_embeddings
        saved_embeddings = get_student_all_embeddings(student.id)
        if len(saved_embeddings) == 0:
            app.logger.error(f"CRITICAL: Student {student_id} created but no embeddings were saved!")
            db.session.delete(student)
            db.session.commit()
            return jsonify({
                'error': 'Failed to save face embeddings. Please try again.',
                'details': 'Embeddings were processed but not persisted to database'
            }), 500
        
        app.logger.info(f"Student registered: {student_id} ({name}) with {len(saved_embeddings)} embeddings verified in database")

        # Enroll in selected courses
        enrolled_courses = []
        for course_id in selected_courses:
            try:
                enrollment = Enrollment(student_id=student.id, course_id=course_id)
                db.session.add(enrollment)
                enrolled_courses.append(course_id)
            except Exception as e:
                app.logger.warning(f"Failed to enroll in course {course_id}: {str(e)}")

        db.session.commit()

        app.logger.info(f"Student {student_id} enrolled in {len(enrolled_courses)} courses")

        message = f'Registration successful! Enrolled in {len(enrolled_courses)} courses with {len(saved_embeddings)} facial embeddings.'

        response_data = {
            'success': True,
            'message': message,
            'student': student.to_dict(),
            'coursesEnrolled': len(enrolled_courses),
            'embeddingsSaved': len(saved_embeddings),
            'totalFrames': result['total_frames'],
            'validFrames': result['valid_frames']
        }

        # Response data already includes all necessary fields above

        return jsonify(response_data), 201

    except Exception as e:
        from app import app
        app.logger.error(f"Registration error: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@registration_bp.route('/api/register/validate-id/<student_id>', methods=['GET'])
def validate_id(student_id):
    """Check if student ID format is valid and not already taken"""
    is_valid_format = validate_student_id(student_id)
    
    from db import get_student_by_student_id
    is_available = get_student_by_student_id(student_id) is None
    
    return jsonify({
        'validFormat': is_valid_format,
        'available': is_available,
        'message': 'Valid and available' if (is_valid_format and is_available) else
                   'Invalid format' if not is_valid_format else 'Already registered'
    }), 200
