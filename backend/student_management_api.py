"""
Student Management API Endpoints
Delete, Update, and View registered students with safety checks
"""
from flask import Blueprint, request, jsonify
from datetime import datetime

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
        student = Student.query.get(student_id)
        
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
        
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            student.name = data['name'].strip()
        if 'rollNumber' in data:
            student.student_id = data['rollNumber'].strip()
        if 'email' in data:
            student.email = data['email'].strip()
        if 'phone' in data:
            student.phone = data['phone'].strip()
        if 'department' in data:
            student.department = data['department'].strip()
        
        student.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Student updated successfully',
            'student': student.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_mgmt_bp.route('/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student and all associated data (embeddings, attendance)"""
    try:
        from db import db, Student
        
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Store info before deletion
        student_name = student.name
        student_id_val = student.id
        
        # Delete cascades to embeddings and attendance records
        db.session.delete(student)
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
        
        student = Student.query.get(student_id)
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
        
        records = Attendance.query.filter_by(student_id=student_id).order_by(
            Attendance.marked_at.desc()
        ).all()
        
        return jsonify({
            'studentId': student_id,
            'studentName': student.name,
            'totalRecords': len(records),
            'attendance': [r.to_dict() for r in records]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
