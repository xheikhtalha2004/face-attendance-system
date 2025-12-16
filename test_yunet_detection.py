"""
YuNet Face Detection Test Script
Tests YuNet detector and compares with other methods
"""
import cv2
import numpy as np
import argparse
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ml_cvs.face_detection import FaceDetector


def draw_faces(image, faces, color=(0, 255, 0), label=""):
    """Draw bounding boxes on image"""
    result = image.copy()
    for i, (x, y, w, h) in enumerate(faces):
        cv2.rectangle(result, (x, y), (x + w, y + h), color, 2)
        text = f"{label} {i+1}" if label else f"Face {i+1}"
        cv2.putText(result, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, color, 2)
    return result


def test_image(image_path, method='yunet', show=True):
    """Test face detection on a single image"""
    print(f"\n{'='*60}")
    print(f"Testing {method.upper()} detector on image")
    print(f"{'='*60}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Failed to load image: {image_path}")
        return None
    
    print(f"✓ Loaded image: {image.shape[1]}x{image.shape[0]}")
    
    # Create detector
    print(f"Initializing {method} detector...")
    detector = FaceDetector(method=method, min_face_size=20)
    
    # Detect faces
    start_time = time.time()
    faces = detector.detect_faces(image)
    elapsed = (time.time() - start_time) * 1000
    
    print(f"✓ Detected {len(faces)} face(s) in {elapsed:.1f}ms")
    
    if faces:
        for i, (x, y, w, h) in enumerate(faces):
            print(f"  Face {i+1}: ({x}, {y}) {w}x{h} pixels")
    
    # Draw results
    result = draw_faces(image, faces, label=method.upper())
    
    if show:
        cv2.imshow(f"{method.upper()} Detection", result)
        print("\nPress any key to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    return faces, result, elapsed


def test_webcam(method='yunet'):
    """Test face detection on webcam feed"""
    print(f"\n{'='*60}")
    print(f"Testing {method.upper()} detector on webcam")
    print(f"{'='*60}")
    print("Press 'q' to quit, 's' to save screenshot")
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Failed to open webcam")
        return
    
    # Create detector
    detector = FaceDetector(method=method, min_face_size=40)
    
    fps_list = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Detect faces
        start_time = time.time()
        faces = detector.detect_faces(frame)
        elapsed = (time.time() - start_time) * 1000
        fps = 1000 / elapsed if elapsed > 0 else 0
        fps_list.append(fps)
        
        # Draw results
        result = draw_faces(frame, faces)
        
        # Add stats
        cv2.putText(result, f"{method.upper()}: {len(faces)} face(s)", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(result, f"FPS: {fps:.1f}", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show
        cv2.imshow(f"{method.upper()} Webcam", result)
        
        # Handle keys
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"yunet_capture_{int(time.time())}.jpg"
            cv2.imwrite(filename, result)
            print(f"✓ Saved screenshot: {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    
    if fps_list:
        avg_fps = np.mean(fps_list)
        print(f"\n✓ Average FPS: {avg_fps:.1f}")
        print(f"  Total frames: {frame_count}")


def compare_methods(image_path):
    """Compare all detection methods on same image"""
    print(f"\n{'='*60}")
    print(f"Comparing all detection methods")
    print(f"{'='*60}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Failed to load image: {image_path}")
        return
    
    methods = ['yunet', 'haar', 'hog']
    results = []
    
    for method in methods:
        try:
            print(f"\nTesting {method.upper()}...")
            detector = FaceDetector(method=method, min_face_size=20)
            
            start_time = time.time()
            faces = detector.detect_faces(image)
            elapsed = (time.time() - start_time) * 1000
            
            print(f"  ✓ Detected {len(faces)} face(s) in {elapsed:.1f}ms")
            
            # Draw results
            result = draw_faces(image, faces, label=method.upper())
            results.append((method, result, len(faces), elapsed))
            
        except Exception as e:
            print(f"  ❌ Failed: {str(e)}")
    
    # Display comparison
    if results:
        # Create comparison grid
        h, w = image.shape[:2]
        
        if len(results) >= 2:
            # Side by side
            combined = np.hstack([r[1] for r in results[:2]])
            cv2.imshow("Comparison (Left: YuNet, Right: Haar)", combined)
            
            print("\n" + "="*60)
            print("COMPARISON SUMMARY")
            print("="*60)
            for method, _, count, ms in results:
                print(f"{method.upper():8s} | Faces: {count:2d} | Time: {ms:6.1f}ms | FPS: {1000/ms if ms > 0 else 0:5.1f}")
            
            print("\nPress any key to close...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()


def benchmark(image_path, iterations=10):
    """Benchmark detection methods"""
    print(f"\n{'='*60}")
    print(f"Benchmarking detection methods ({iterations} iterations)")
    print(f"{'='*60}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Failed to load image: {image_path}")
        return
    
    methods = ['yunet', 'haar', 'hog']
    
    print(f"\nImage size: {image.shape[1]}x{image.shape[0]}\n")
    
    for method in methods:
        try:
            print(f"Testing {method.upper()}...")
            detector = FaceDetector(method=method, min_face_size=20)
            
            times = []
            face_counts = []
            
            for i in range(iterations):
                start_time = time.time()
                faces = detector.detect_faces(image)
                elapsed = (time.time() - start_time) * 1000
                times.append(elapsed)
                face_counts.append(len(faces))
            
            avg_time = np.mean(times)
            std_time = np.std(times)
            avg_faces = np.mean(face_counts)
            fps = 1000 / avg_time
            
            print(f"  ✓ Avg time: {avg_time:.2f}ms ± {std_time:.2f}ms")
            print(f"  ✓ Avg FPS: {fps:.1f}")
            print(f"  ✓ Avg faces: {avg_faces:.1f}")
            print()
            
        except Exception as e:
            print(f"  ❌ Failed: {str(e)}\n")


def main():
    parser = argparse.ArgumentParser(description="YuNet Face Detection Test")
    parser.add_argument('--method', type=str, default='yunet',
                        choices=['yunet', 'haar', 'hog'],
                        help='Detection method')
    parser.add_argument('--image', type=str,
                        help='Path to test image')
    parser.add_argument('--webcam', action='store_true',
                        help='Test on webcam')
    parser.add_argument('--compare', action='store_true',
                        help='Compare all methods')
    parser.add_argument('--benchmark', action='store_true',
                        help='Benchmark all methods')
    parser.add_argument('--iterations', type=int, default=10,
                        help='Benchmark iterations')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("YuNet Face Detection Test Script")
    print("="*60)
    
    if args.webcam:
        test_webcam(args.method)
    elif args.compare and args.image:
        compare_methods(args.image)
    elif args.benchmark and args.image:
        benchmark(args.image, args.iterations)
    elif args.image:
        test_image(args.image, args.method)
    else:
        # Default: test with webcam
        print("\nNo arguments provided. Testing with webcam...")
        print("Use --help to see all options")
        test_webcam('yunet')


if __name__ == "__main__":
    main()
