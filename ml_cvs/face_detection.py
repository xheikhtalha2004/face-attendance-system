"""
Face Detection Module
Implements face detection using OpenCV (per SRDS specification)
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional


class FaceDetector:
    """Face detection using OpenCV Haar Cascades and HOG"""
    
    def __init__(self, method='hog', min_face_size=20):
        """
        Initialize face detector
        
        Args:
            method: 'haar' or 'hog' detection method
            min_face_size: Minimum face size to detect
        """
        self.method = method
        self.min_face_size = min_face_size
        
        if method == 'haar':
            # Load Haar Cascade classifier
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in image
        
        Args:
            image: Input image (BGR or RGB format)
            
        Returns:
            List of face bounding boxes as (x, y, width, height)
        """
        if image is None or image.size == 0:
            return []
        
        # Convert to grayscale for detection
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        if self.method == 'haar':
            faces = self._detect_haar(gray)
        else:
            faces = self._detect_hog(image)
        
        # Filter by min face size
        filtered_faces = []
        for (x, y, w, h) in faces:
            if w >= self.min_face_size and h >= self.min_face_size:
                filtered_faces.append((x, y, w, h))
        
        return filtered_faces
    
    def _detect_haar(self, gray_image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces using Haar Cascade"""
        faces = self.face_cascade.detectMultiScale(
            gray_image,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(self.min_face_size, self.min_face_size)
        )
        return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
    
    def _detect_hog(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces using HOG (via face_recognition library)"""
        try:
            import face_recognition
            
            # Convert BGR to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image
            
            # Detect faces
            face_locations = face_recognition.face_locations(rgb_image, model='hog')
            
            # Convert from (top, right, bottom, left) to (x, y, w, h)
            faces = []
            for (top, right, bottom, left) in face_locations:
                x, y = left, top
                w, h = right - left, bottom - top
                faces.append((x, y, w, h))
            
            return faces
        except ImportError:
            print("Warning: face_recognition not available, falling back to Haar")
            return self._detect_haar(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
    
    def get_face_locations(self, image: np.ndarray) -> List[dict]:
        """
        Get face locations with normalized coordinates
        
        Returns:
            List of dicts with face location info
        """
        faces = self.detect_faces(image)
        height, width = image.shape[:2]
        
        face_locations = []
        for i, (x, y, w, h) in enumerate(faces):
            face_locations.append({
                'index': i,
                'box': {
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h)
                },
                'normalized': {
                    'x': x / width,
                    'y': y / height,
                    'width': w / width,
                    'height': h / height
                }
            })
        
        return face_locations
    
    def extract_face_region(self, image: np.ndarray, location: Tuple[int, int, int, int], 
                           padding: float = 0.2) -> Optional[np.ndarray]:
        """
        Extract face region from image with optional padding
        
        Args:
            image: Source image
            location: Face location as (x, y, width, height)
            padding: Padding ratio (0.2 = 20% padding on each side)
            
        Returns:
            Cropped face image or None if invalid
        """
        if image is None or location is None:
            return None
        
        x, y, w, h = location
        height, width = image.shape[:2]
        
        # Add padding
        pad_w = int(w * padding)
        pad_h = int(h * padding)
        
        # Calculate padded coordinates
        x1 = max(0, x - pad_w)
        y1 = max(0, y - pad_h)
        x2 = min(width, x + w + pad_w)
        y2 = min(height, y + h + pad_h)
        
        # Extract face
        face_image = image[y1:y2, x1:x2]
        
        if face_image.size == 0:
            return None
        
        return face_image
    
    def check_image_quality(self, image: np.ndarray) -> dict:
        """
        Check image quality for face recognition
        
        Returns:
            Dict with quality metrics
        """
        if image is None or image.size == 0:
            return {'valid': False, 'reason': 'Empty image'}
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Check blur (Laplacian variance)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        is_blurry = blur_score < 100  # Threshold for blur detection
        
        # Check brightness
        mean_brightness = np.mean(gray)
        is_too_dark = mean_brightness < 50
        is_too_bright = mean_brightness > 200
        
        # Check size
        height, width = gray.shape
        is_too_small = height < 100 or width < 100
        
        quality = {
            'valid': not (is_blurry or is_too_dark or is_too_bright or is_too_small),
            'blur_score': float(blur_score),
            'brightness': float(mean_brightness),
            'is_blurry': is_blurry,
            'is_too_dark': is_too_dark,
            'is_too_bright': is_too_bright,
            'is_too_small': is_too_small,
            'dimensions': (height, width)
        }
        
        if not quality['valid']:
            reasons = []
            if is_blurry:
                reasons.append('Image is too blurry')
            if is_too_dark:
                reasons.append('Image is too dark')
            if is_too_bright:
                reasons.append('Image is too bright')
            if is_too_small:
                reasons.append('Image is too small')
            quality['reason'] = ', '.join(reasons)
        
        return quality


def detect_faces(image: np.ndarray, method='hog', min_size=20) -> List[Tuple[int, int, int, int]]:
    """
    Convenience function to detect faces
    
    Args:
        image: Input image
        method: Detection method ('haar' or 'hog')
        min_size: Minimum face size
        
    Returns:
        List of face locations as (x, y, w, h)
    """
    detector = FaceDetector(method=method, min_face_size=min_size)
    return detector.detect_faces(image)


def extract_face(image: np.ndarray, location: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
    """
    Convenience function to extract face region
    
    Args:
        image: Input image
        location: Face location (x, y, w, h)
        
    Returns:
        Cropped face image
    """
    detector = FaceDetector()
    return detector.extract_face_region(image, location)
