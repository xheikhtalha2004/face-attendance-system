"""
Student Management API Endpoints
Delete, Update, and View registered students with safety checks
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

student_mgmt_bp = Blueprint('student_management', __name__, url_prefix='/api/students')


@student_mgmt_bp.route('', methods=['GET'])
def get_all_students():
    """Get all registered students"""
    try:
        from db_helpers import get_all_students
        students = get_all_students()
        
        return jsonify([s.to_dict() for s in students]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_mgmt_bp.route('/<int:student_id>', methods=['GET'])
def get_student_detail(student_id):
    """Get detailed student information"""
    try:
        from db import Student
        student = Student.query.filter_by(id=student_id, deleted_at=None).first()
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        return jsonify(student.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_mgmt_bp.route('/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """Update student information (name, roll number, email, phone)"""
    try:
        from db import db, Student
        
        student = Student.query.filter_by(id=student_id, deleted_at=None).first()
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate roll number uniqueness (exclude soft-deleted students)
        if 'rollNumber' in data and data['rollNumber']:
            proposed_roll = data['rollNumber'].strip()
            if Student.query.filter(
                Student.student_id == proposed_roll,
                Student.id != student_id,
                Student.deleted_at == None
            ).first():
                return jsonify({'error': f'Roll number {proposed_roll} already exists'}), 409

        # Validate email format if provided
        if 'email' in data and data['email']:
            if not EMAIL_REGEX.match(data['email'].strip()):
                return jsonify({'error': 'Invalid email format'}), 400
        
        # Update allowed fields
        if 'name' in data and data['name']:
            student.name = data['name'].strip()
        if 'rollNumber' in data and data['rollNumber']:
            student.student_id = data['rollNumber'].strip()
        if 'email' in data and data['email']:
            student.email = data['email'].strip()
        if 'phone' in data and data['phone']:
            student.phone = data['phone'].strip()
        if 'department' in data and data['department']:
            student.department = data['department'].strip()
        
        student.updated_at = datetime.utcnow()
        try:
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            return jsonify({'error': 'Constraint violation', 'details': str(ie.orig)}), 409
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Database error', 'details': str(e)}), 500
        
        return jsonify({
            'message': 'Student updated successfully',
            'student': student.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_mgmt_bp.route('/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Soft delete a student (mark as deleted, keeps record for history)"""
    try:
        from db import db, Student
        from datetime import datetime
        
        student = Student.query.filter_by(id=student_id, deleted_at=None).first()
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Store info before deletion
        student_name = student.name
        student_id_val = student.id
        
        # Soft delete - just set deleted_at timestamp
        student.deleted_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': f'Student {student_name} (ID: {student_id_val}) deleted successfully',
            'deletedStudent': {
                'id': student_id_val,
                'name': student_name
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_mgmt_bp.route('/<int:student_id>/embeddings', methods=['GET'])
def get_student_embeddings(student_id):
    """Get all face embeddings for a student"""
    try:
        from db import Student, StudentEmbedding
        
        student = Student.query.filter_by(id=student_id, deleted_at=None).first()
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        embeddings = StudentEmbedding.query.filter_by(student_id=student_id).all()
        
        return jsonify({
            'studentId': student_id,
            'studentName': student.name,
            'totalEmbeddings': len(embeddings),
            'embeddings': [{
                'id': e.id,
                'qualityScore': e.quality_score,
                'createdAt': e.created_at.isoformat()
            } for e in embeddings]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_mgmt_bp.route('/<int:student_id>/attendance-records', methods=['GET'])
def get_student_attendance(student_id):
    """Get all attendance records for a student"""
    try:
        from db import Student, Attendance
        
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        records = Attendance.query.filter_by(student_id_fk=student_id).order_by(
            Attendance.check_in_time.desc()
        ).all()
        
        return jsonify({
            'studentId': student_id,
            'studentName': student.name,
            'totalRecords': len(records),
            'attendance': [r.to_dict() for r in records]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
