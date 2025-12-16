"""
Debug Face Registration
Quick diagnostic script to test face processing pipeline
"""
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ml_cvs'))

print("=" * 60)
print("FACE REGISTRATION DIAGNOSTIC")
print("=" * 60)

# Test 1: Check if ML models are available
print("\n[1] Checking ML/CV dependencies...")
try:
    import cv2
    print("✓ OpenCV imported successfully")
except ImportError as e:
    print(f"✗ OpenCV import failed: {e}")
    sys.exit(1)

try:
    import numpy as np
    print("✓ NumPy imported successfully")
except ImportError as e:
    print(f"✗ NumPy import failed: {e}")
    sys.exit(1)

# Test 2: Check if face engine can be initialized
print("\n[2] Initializing face engine...")
try:
    from ml_cvs.face_engine import FaceEngine
    face_engine = FaceEngine()
    print("✓ Face engine initialized successfully")
except ImportError as e:
    print(f"✗ Face engine import failed: {e}")
    print("   → InsightFace may not be installed")
    sys.exit(1)
except Exception as e:
    print(f"✗ Face engine initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check if enrollment service can process frames
print("\n[3] Testing enrollment service...")
try:
    from enrollment_service import process_enrollment_frames
    print("✓ Enrollment service imported successfully")
except ImportError as e:
    print(f"✗ Enrollment service import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Create a simple test image
print("\n[4] Creating test image with simulated face...")
test_image = np.zeros((480, 640, 3), dtype=np.uint8)
# Draw a simple face-like pattern
cv2.circle(test_image, (320, 240), 100, (255, 255, 255), -1)  # Face
cv2.circle(test_image, (280, 220), 15, (0, 0, 0), -1)  # Left eye
cv2.circle(test_image, (360, 220), 15, (0, 0, 0), -1)  # Right eye
cv2.ellipse(test_image, (320, 270), (40, 20), 0, 0, 180, (0, 0, 0), 2)  # Smile

# Test 5: Try to detect faces in test image
print("\n[5] Testing face detection...")
try:
    faces = face_engine.detect_faces(test_image)
    if faces:
        print(f"✓ Face detection working (detected {len(faces)} face(s))")
    else:
        print("⚠ No faces detected in test image (expected - this is a simple drawing)")
        print("   → This is normal. Real face images should work.")
except Exception as e:
    print(f"✗ Face detection failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Check database connection
print("\n[6] Testing database connection...")
try:
    from app import app
    from db import db, Student, StudentEmbedding
    
    with app.app_context():
        student_count = Student.query.count()
        embedding_count = StudentEmbedding.query.count()
        print(f"✓ Database connection successful")
        print(f"   → Total students: {student_count}")
        print(f"   → Total embeddings: {embedding_count}")
        
        # Show students with embedding counts
        if student_count > 0:
            print("\n   Student Embedding Status:")
            students = Student.query.all()
            for s in students:
                emb_count = len(s.embeddings)
                status = "✓" if emb_count > 0 else "✗"
                print(f"   {status} {s.student_id} ({s.name}): {emb_count} embeddings")
                
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print("\nIf all tests pass, the face processing pipeline should work.")
print("If students still have 0 embeddings after registration, check:")
print("1. Frontend is sending valid base64 image frames")
print("2. Images contain clear, frontal faces")
print("3. Backend logs for specific error messages")
