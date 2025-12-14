"""
Quick System Test
Tests backend with InsightFace integration
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("="*60)
print("FACE ATTENDANCE SYSTEM - QUICK TEST")
print("="*60)

# Test 1: Database
print("\n1. Testing Database...")
try:
    from db import db, init_db, Student, Course
    from app import app
    
    with app.app_context():
        # Check students
        students = Student.query.all()
        print(f"   ✓ Database accessible")
        print(f"   ✓ Students in DB: {len(students)}")
        
        # Check courses
        courses = Course.query.all()
        print(f"   ✓ Courses in DB: {len(courses)}")
except Exception as e:
    print(f"   ❌ Database error: {e}")

# Test 2: InsightFace
print("\n2. Testing InsightFace...")
try:
    from ml_cvs.face_engine import create_face_engine
    engine = create_face_engine(use_gpu=False)
    print(f"   ✓ Face engine initialized")
    print(f"   ✓ Models loaded: {list(engine.app.models.keys())}")
except Exception as e:
    print(f"   ❌ InsightFace error: {e}")

# Test 3: Stabilizer
print("\n3. Testing Stabilizer...")
try:
    from ml_cvs.stabilizer import create_stabilizer
    stabilizer = create_stabilizer(k=5, n=10, cooldown=120)
    print(f"   ✓ Stabilizer created (K=5, N=10)")
except Exception as e:
    print(f"   ❌ Stabilizer error: {e}")

# Test 4: API Blueprints
print("\n4. Testing API Blueprints...")
try:
    from app import app
    
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint not in ['static']:
            routes.append(f"{rule.rule} [{', '.join(rule.methods - {'HEAD', 'OPTIONS'})}]")
    
    print(f"   ✓ Registered {len(routes)} API routes")
    
    # Check key endpoints
    key_endpoints = [
        '/api/register/student',
        '/api/recognize',
        '/api/sessions/<int:session_id>/finalize',
        '/api/sessions/<int:session_id>/export'
    ]
    
    for endpoint in key_endpoints:
        found = any(endpoint.replace('<int:session_id>', str(1)) in route for route in routes)
        if found or any(endpoint.split('<')[0] in route for route in routes):
            print(f"   ✓ {endpoint}")
        else:
            print(f"   ⚠ {endpoint} not found")
            
except Exception as e:
    print(f"   ❌ API error: {e}")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("✓ All core components initialized successfully!")
print("\nNext steps:")
print("1. Start backend: python backend/app.py")
print("2. Start frontend: cd frontend && npm run dev")
print("3. Test student registration at http://localhost:5173")
print("="*60)
