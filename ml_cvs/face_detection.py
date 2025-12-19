"""
Face Detection Module - YuNet Only
Uses OpenCV's YuNet DNN-based face detector (fast, accurate, no external dependencies)
"""
import cv2
import numpy as np
import os
from typing import List, Tuple, Optional, Dict
from pathlib import Path


class FaceDetector:
    """Face detection using YuNet DNN model only"""
    
    def __init__(self, min_face_size=40, score_threshold=0.9, nms_threshold=0.3, top_k=5000):
        """
        Initialize YuNet face detector
        
        Args:
            min_face_size: Minimum face size to detect (pixels), default 40
            score_threshold: Detection confidence threshold (0-1), default 0.9
            nms_threshold: Non-maximum suppression threshold, default 0.3
            top_k: Max detections before NMS, default 5000
        """
        self.min_face_size = min_face_size
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.top_k = top_k
        self.yunet_detector = None
        
        # Initialize YuNet detector
        self._init_yunet()
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in image using YuNet
        
        Args:
            image: Input image (BGR format from OpenCV)
            
        Returns:
            List of face bounding boxes as (x, y, width, height)
        """
        if image is None or image.size == 0:
            return []
        
        faces = self._detect_yunet(image)
        
        # Filter by min face size
        filtered_faces = []
        for (x, y, w, h) in faces:
            if w >= self.min_face_size and h >= self.min_face_size:
                filtered_faces.append((x, y, w, h))
        
        return filtered_faces
    
    def _init_yunet(self):
        """Initialize YuNet detector with model auto-download"""
        try:
            from ml_cvs.models.yunet_utils import get_yunet_model_path, check_yunet_compatibility
            
            # Check OpenCV compatibility
            if not check_yunet_compatibility():
                raise RuntimeError("OpenCV version does not support YuNet (requires >= 4.8)")
            
            # Get model path (auto-download if needed)
            model_path = get_yunet_model_path(auto_download=True)
            if not model_path:
                raise RuntimeError("Failed to obtain YuNet model file")
            
            # Create detector with initial input size (will be updated per frame)
            self.yunet_detector = cv2.FaceDetectorYN.create(
                model_path,
                "",
                (320, 320),
                score_threshold=self.score_threshold,
                nms_threshold=self.nms_threshold,
                top_k=self.top_k
            )
            
            print(f"[OK] YuNet detector initialized (score_threshold={self.score_threshold})")

        except Exception as e:
            print(f"[ERROR] Failed to initialize YuNet: {str(e)}")
            raise
    
    def _detect_yunet(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using YuNet DNN model
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            List of face bounding boxes as (x, y, w, h)
        """
        if self.yunet_detector is None:
            raise RuntimeError("YuNet detector not initialized")
        
        # Get image dimensions
        height, width = image.shape[:2]
        
        # Update input size for this frame (YuNet needs this for accurate detection)
        self.yunet_detector.setInputSize((width, height))
        
        # Detect faces
        # Returns: None if no faces, or array with shape (num_faces, 15)
        # Each row: [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rcm, y_rcm, x_lcm, y_lcm, score]
        # where re=right eye, le=left eye, nt=nose tip, rcm=right corner mouth, lcm=left corner mouth
        _, faces_data = self.yunet_detector.detect(image)
        
        if faces_data is None:
            return []
        
        # Extract bounding boxes and convert to (x, y, w, h)
        faces = []
        for face in faces_data:
            x, y, w, h = face[:4]
            # Convert to integers
            x, y, w, h = int(x), int(y), int(w), int(h)
            faces.append((x, y, w, h))
        
        return faces
    
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


def detect_faces(image: np.ndarray, min_size=20) -> List[Tuple[int, int, int, int]]:
    """
    Convenience function to detect faces
    
    Args:
        image: Input image
        min_size: Minimum face size
        
    Returns:
        List of face locations as (x, y, w, h)
    """
    detector = FaceDetector(min_face_size=min_size)
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
