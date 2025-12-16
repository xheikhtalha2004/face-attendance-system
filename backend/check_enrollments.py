"""Check student enrollment"""
import sys
sys.path.insert(0, 'backend')

from db import db, Student, Enrollment, Course, Session
from app import app

with app.app_context():
    # Check which courses students are enrolled in
    students = Student.query.all()
    print("=" * 60)
    print("STUDENT ENROLLMENTS")
    print("=" * 60)
    
    for s in students:
        enrollments = Enrollment.query.filter_by(student_id=s.id).all()
        print(f"\n{s.student_id} ({s.name}):")
        print(f"  Embeddings: {len(s.embeddings)}")
        if enrollments:
            for e in enrollments:
                course = Course.query.get(e.course_id)
                print(f"  - Enrolled in Course {e.course_id}: {course.course_name}")
        else:
            print("  - NO ENROLLMENTS")
    
    # Check active session
    print("\n" + "=" * 60)
    print("ACTIVE SESSION")
    print("=" * 60)
    active = Session.query.filter_by(status='ACTIVE').first()
    if active:
        print(f"Course ID: {active.course_id}")
        print(f"Course Name: {active.course.course_name}")
        print(f"Professor: {active.course.professor_name}")
    else:
        print("No active session")
