"""
Helper script to clean up students without embeddings
Run this after fixing the registration endpoint
"""
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from db import db, Student, StudentEmbedding

print("=" * 60)
print("CLEANUP: Students Without Embeddings")
print("=" * 60)

with app.app_context():
    # Find students without embeddings
    all_students = Student.query.all()
    
    students_without_embeddings = []
    for student in all_students:
        emb_count = len(student.embeddings)
        if emb_count == 0:
            students_without_embeddings.append(student)
            print(f"\n⚠ {student.student_id} ({student.name})")
            print(f"   Department: {student.department}")
            print(f"   Email: {student.email}")
            print(f"   Embeddings: {emb_count}")
    
    if not students_without_embeddings:
        print("\n✓ All students have embeddings!")
    else:
        print(f"\n\nFound {len(students_without_embeddings)} student(s) without embeddings.")
        print("\nRECOMMENDATIONS:")
        print("1. Delete these students and have them re-register through the frontend")
        print("2. This will use the new fixed registration flow that ensures embeddings are saved")
        
        response = input(f"\nDo you want to DELETE these {len(students_without_embeddings)} student(s)? (yes/no): ")
        
        if response.lower() == 'yes':
            for student in students_without_embeddings:
                print(f"Deleting: {student.student_id} ({student.name})")
                db.session.delete(student)
            
            db.session.commit()
            print(f"\n✓ Deleted {len(students_without_embeddings)} student(s)")
            print("These students can now re-register with proper face enrollment.")
        else:
            print("\nNo changes made. Students remain in database.")

print("\n" + "=" * 60)
