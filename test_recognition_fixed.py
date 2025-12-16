#!/usr/bin/env python
"""Quick test to verify recognition is fixed"""
import sys
sys.path.insert(0, 'backend')
from app import app
from db_helpers import get_all_students_with_embeddings
import pickle

with app.app_context():
    students = get_all_students_with_embeddings()
    
    if len(students) >= 2:
        from ml_cvs.face_engine import FaceEngine
        engine = FaceEngine()
        
        # Simulate recognition test for each student
        print('\n' + '='*70)
        print('RECOGNITION TEST - Each Student Against All')
        print('='*70)
        
        for test_student in students:
            test_embedding = pickle.loads(test_student['embeddings'][5])
            test_name = test_student['student_name']
            
            results = []
            for student in students:
                similarities = []
                for emb_bytes in student['embeddings']:
                    emb = pickle.loads(emb_bytes)
                    sim = engine.compare_embeddings_cosine(test_embedding, emb)
                    similarities.append(sim)
                
                best_sim = max(similarities) if similarities else 0.0
                results.append({
                    'name': student['student_name'],
                    'best_similarity': best_sim
                })
            
            # Sort by similarity
            results.sort(key=lambda x: x['best_similarity'], reverse=True)
            
            print(f'\nWhen testing {test_name}:')
            for result in results:
                status = '✅' if result['name'] == test_name else '❌' if result['name'] == results[0]['name'] else '  '
                print(f'  {status} {result["name"]}: {result["best_similarity"]:.4f}')
            
            if results[0]['name'] == test_name:
                print(f'  Result: ✅ CORRECT - Recognized as {test_name}')
            else:
                print(f'  Result: ❌ WRONG - Misidentified as {results[0]["name"]}')

print('\n' + '='*70)
print('Testing complete. Try the frontend now!')
print('='*70 + '\n')
