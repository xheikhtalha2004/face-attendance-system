"""
Quick Start Script for YuNet Face Detection
Downloads the model and runs a basic test
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*60)
print("YuNet Face Detection - Quick Start")
print("="*60)

print("\n1. Checking OpenCV compatibility...")
from ml_cvs.models.yunet_utils import check_yunet_compatibility
if not check_yunet_compatibility():
    print("\n❌ Your OpenCV version doesn't support YuNet")
    print("Please upgrade: pip install --upgrade opencv-python>=4.8")
    sys.exit(1)

print("\n2. Downloading YuNet model...")
from ml_cvs.models.yunet_utils import get_yunet_model_path
model_path = get_yunet_model_path(auto_download=True)
if not model_path:
    print("\n❌ Failed to download model")
    sys.exit(1)

print(f"\n✓ Model ready at: {model_path}")

print("\n3. Testing YuNet detector...")
from ml_cvs.face_detection import FaceDetector
import cv2
import numpy as np

# Create a simple test with webcam
print("\nOpening webcam for live detection test...")
print("Press 'q' to quit")

detector = FaceDetector(min_face_size=40)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Failed to open webcam")
    print("You can test with an image using:")
    print("  python test_yunet_detection.py --image path/to/image.jpg")
    sys.exit(1)

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Detect faces
    faces = detector.detect_faces(frame)
    
    # Draw boxes
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    # Add info
    cv2.putText(frame, f"YuNet: {len(faces)} face(s)", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, "Press 'q' to quit", 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.imshow('YuNet Face Detection', frame)
    
    frame_count += 1
    if frame_count == 1:
        print("✓ Detection working! Close the window or press 'q' to exit")
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("\n" + "="*60)
print("✓ YuNet setup complete!")
print("="*60)
print("\nNext steps:")
print("  • Test with image: python test_yunet_detection.py --image photo.jpg")
print("  • Compare methods: python test_yunet_detection.py --compare --image photo.jpg")
print("  • Benchmark: python test_yunet_detection.py --benchmark --image photo.jpg")
print("  • See all options: python test_yunet_detection.py --help")
