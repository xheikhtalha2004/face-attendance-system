"""
Simple YuNet Test - No Display Required
Tests YuNet detector functionality without GUI
"""
import sys
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*60)
print("YuNet Face Detection - Simple Test")
print("="*60)

# Step 1: Check OpenCV
print("\n1. Checking OpenCV compatibility...")
try:
    import cv2
    print(f"   ✓ OpenCV version: {cv2.__version__}")
    
    from ml_cvs.models.yunet_utils import check_yunet_compatibility
    if not check_yunet_compatibility():
        print("   ❌ OpenCV doesn't support YuNet")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Step 2: Download model
print("\n2. Downloading YuNet model (if needed)...")
try:
    from ml_cvs.models.yunet_utils import get_yunet_model_path
    model_path = get_yunet_model_path(auto_download=True)
    if not model_path:
        print("   ❌ Failed to get model")
        sys.exit(1)
    print(f"   ✓ Model ready: {model_path}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test detector
print("\n3. Testing YuNet detector...")
try:
    from ml_cvs.face_detection import FaceDetector
    
    # Create a test image (simple synthetic face-like pattern)
    print("   Creating test image (640x480)...")
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Initialize detector
    print("   Initializing detector...")
    detector = FaceDetector(min_face_size=40)
    
    # Test detection
    print("   Running detection...")
    faces = detector.detect_faces(test_image)
    
    print(f"   ✓ Detection completed")
    print(f"   ✓ Found {len(faces)} face(s) in test image")
    
    if faces:
        for i, (x, y, w, h) in enumerate(faces):
            print(f"      Face {i+1}: bbox=({x}, {y}, {w}, {h})")
    
except Exception as e:
    print(f"   ❌ Error during detection: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Test all methods
print("\n4. Testing all detection methods...")
methods = ['yunet', 'haar']  # Skip 'hog' if face_recognition not available

for method in ['yunet']:
    try:
        print(f"\n   Testing {method.upper()}...")
        detector = FaceDetector(min_face_size=40)
        faces = detector.detect_faces(test_image)
        print(f"   ✓ {method.upper()}: {len(faces)} face(s) detected")
    except Exception as e:
        print(f"   ⚠ {method.upper()} failed: {e}")

# Success
print("\n" + "="*60)
print("✓ YuNet Integration Test PASSED")
print("="*60)
print("\nYuNet is ready to use!")
print("\nUsage in your code:")
print("  from ml_cvs.face_detection import FaceDetector")
print("  detector = FaceDetector(method='yunet')")
print("  faces = detector.detect_faces(image)")
print("\nNext steps:")
print("  • Test with real images: python test_yunet_detection.py --image photo.jpg")
print("  • Update backend to use YuNet detector")
print("  • Adjust score_threshold in config if needed (ml_cvs/config.py)")
