"""
Database Cleanup Script - Simple Version
Safely remove all students and their associated data
"""
import sys
import os

# Change to backend directory
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from db import db, Student, StudentEmbedding, Attendance
from app import app

print("="*60)
print("Database Cleanup Tool")
print("="*60)

with app.app_context():
    # Get all students
    students = Student.query.all()
    
    if not students:
        print("\n✓ Database is already empty!")
        sys.exit(0)
    
    print(f"\nFound {len(students)} student(s) in database:")
    print("-"*60)
    
    for student in students:
        # Count embeddings
        embedding_count = StudentEmbedding.query.filter_by(student_id=student.id).count()
        # Count attendance records
        attendance_count = Attendance.query.filter_by(student_id_fk=student.id).count()
        
        print(f"\n• Student ID: {student.student_id}")
        print(f"  Name: {student.name}")
        print(f"  Department: {student.department or 'N/A'}")
        print(f"  Email: {student.email or 'N/A'}")
        print(f"  Embeddings: {embedding_count}")
        print(f"  Attendance: {attendance_count}")
    
    print("\n" + "="*60)
    
    # Ask for confirmation
    response = input("\n⚠️  Delete ALL students and their data? (yes/no): ").strip().lower()
    
    if response == 'yes':
        print("\nDeleting data...")
        
        deleted_students = 0
        deleted_embeddings = 0
        deleted_attendance = 0
        
        for student in students:
            # Delete embeddings
            embeddings = StudentEmbedding.query.filter_by(student_id=student.id).all()
            for emb in embeddings:
                db.session.delete(emb)
                deleted_embeddings += 1
            
            # Delete attendance records  
            attendance_records = Attendance.query.filter_by(student_id_fk=student.id).all()
            for att in attendance_records:
                db.session.delete(att)
                deleted_attendance += 1
            
            # Delete student
            db.session.delete(student)
            deleted_students += 1
        
        # Commit all deletions
        db.session.commit()
        
        print(f"\n✓ Deleted {deleted_students} student(s)")
        print(f"✓ Deleted {deleted_embeddings} embedding(s)")
        print(f"✓ Deleted {deleted_attendance} attendance record(s)")
        print("\n✅ Database cleaned successfully!")
        print("\nYou can now register students again.")
        
    else:
        print("\n❌ Cleanup cancelled")
