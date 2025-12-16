#!/usr/bin/env python
"""Debug script to analyze student embeddings and similarities"""
import sys
sys.path.insert(0, 'backend')

from app import app, db
from db_helpers import get_all_students_with_embeddings
import pickle
import numpy as np

print('='*70)
print('DEBUGGING - Student Enrollment Analysis')
print('='*70)

with app.app_context():
    students = get_all_students_with_embeddings()
    
    print(f'\nTotal students: {len(students)}')
    
    for i, student in enumerate(students):
        print(f'\n{i+1}. {student["student_name"]} (ID: {student["student_id"]})')
        print(f'   Embeddings stored: {len(student["embeddings"])}')
        
        # Show embedding characteristics
        for j, emb_bytes in enumerate(student['embeddings']):
            try:
                emb = pickle.loads(emb_bytes)
                print(f'   Embedding {j+1}: shape={emb.shape}, dtype={emb.dtype}, mean={np.mean(emb):.6f}, std={np.std(emb):.6f}')
            except Exception as e:
                print(f'   Embedding {j+1}: ERROR - {e}')
    
    # Test similarity between students
    if len(students) >= 2:
        print('\n' + '='*70)
        print('SIMILARITY TEST - Between Students')
        print('='*70)
        
        from ml_cvs.face_engine import FaceEngine
        engine = FaceEngine()
        
        for i in range(len(students)):
            for j in range(i+1, len(students)):
                emb1 = pickle.loads(students[i]['embeddings'][0])
                emb2 = pickle.loads(students[j]['embeddings'][0])
                
                similarity = engine.compare_embeddings_cosine(emb1, emb2)
                print(f'{students[i]["student_name"]} vs {students[j]["student_name"]}: {similarity:.4f}')
        
        # Test same student embeddings
        print('\n' + '='*70)
        print('SIMILARITY TEST - Same Student (Multiple Embeddings)')
        print('='*70)
        
        for student in students:
            if len(student['embeddings']) >= 2:
                emb1 = pickle.loads(student['embeddings'][0])
                emb2 = pickle.loads(student['embeddings'][1])
                similarity = engine.compare_embeddings_cosine(emb1, emb2)
                print(f'{student["student_name"]} (emb1 vs emb2): {similarity:.4f}')

print('\n' + '='*70)
