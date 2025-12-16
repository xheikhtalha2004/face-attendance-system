#!/usr/bin/env python
"""Debug script to check if embeddings are actually different"""
import sys
sys.path.insert(0, 'backend')

from app import app, db
from db_helpers import get_all_students_with_embeddings
import pickle
import numpy as np

print('='*70)
print('DEBUGGING - Embedding Content Analysis')
print('='*70)

with app.app_context():
    students = get_all_students_with_embeddings()
    
    if len(students) >= 2:
        # Get first embedding of each student
        emb1_bytes = students[0]['embeddings'][0]
        emb2_bytes = students[1]['embeddings'][0]
        
        emb1 = pickle.loads(emb1_bytes)
        emb2 = pickle.loads(emb2_bytes)
        
        print(f'\nStudent 1: {students[0]["student_name"]}')
        print(f'Embedding 1 first 10 values: {emb1[:10]}')
        print(f'Embedding 1 values are unique: {len(np.unique(emb1)) > 1}')
        
        print(f'\nStudent 2: {students[1]["student_name"]}')
        print(f'Embedding 2 first 10 values: {emb2[:10]}')
        print(f'Embedding 2 values are unique: {len(np.unique(emb2)) > 1}')
        
        print(f'\nAre embeddings identical?')
        print(f'Direct comparison: {np.allclose(emb1, emb2)}')
        print(f'Same bytes? {emb1_bytes == emb2_bytes}')
        
        # Check L2 norm (ArcFace embeddings should be ~1.0)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        print(f'\nL2 norms (should be ~1.0 for normalized embeddings):')
        print(f'Student 1: {norm1:.6f}')
        print(f'Student 2: {norm2:.6f}')
        
        # Correct cosine similarity calculation
        dot_product = np.dot(emb1, emb2)
        correct_cosine = dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0
        
        print(f'\nCorrect Cosine Similarity (normalized): {correct_cosine:.6f}')
        print(f'Simple dot product (assumes normalized): {dot_product:.6f}')

print('\n' + '='*70)
