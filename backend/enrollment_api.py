"""
Enrollment Management API
Get enrollment information for students and courses
"""
from flask import Blueprint, jsonify
from db import db, Enrollment, Student, Course

enrollment_bp = Blueprint('enrollment', __name__)

@enrollment_bp.route('/api/enrollments/student/<int:student_id>', methods=['GET'])
def get_student_enrollments(student_id):
    """
    Get all courses a student is enrolled in
    Returns: List of course objects
    """
    try:
        enrollments = Enrollment.query.filter_by(student_id=student_id).all()
        courses = []
        for e in enrollments:
            course = Course.query.get(e.course_id)
            if course:
                courses.append(course.to_dict())
        
        return jsonify(courses), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@enrollment_bp.route('/api/enrollments/course/<int:course_id>', methods=['GET'])
def get_course_enrollments(course_id):
    """
    Get all students enrolled in a course
    Returns: List of student objects
    """
    try:
        enrollments = Enrollment.query.filter_by(course_id=course_id).all()
        students = []
        for e in enrollments:
            student = Student.query.get(e.student_id)
            if student:
                students.append(student.to_dict())
        
        return jsonify(students), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@enrollment_bp.route('/api/enrollments', methods=['GET'])
def get_all_enrollments():
    """
    Get all enrollments (for admin view)
    Returns: List of enrollment objects with student and course info
    """
    try:
        enrollments = Enrollment.query.all()
        return jsonify([e.to_dict() for e in enrollments]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
