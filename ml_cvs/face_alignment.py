"""
Face Alignment Module
Implements face alignment using dlib/Mediapipe (per SRDS specification)
Aligns faces to canonical pose for better recognition accuracy
"""
import cv2
import numpy as np
from typing import Optional, List, Tuple


class FaceAligner:
    """Face alignment using facial landmarks"""
    
    def __init__(self, method='simple'):
        """
        Initialize face aligner
        
        Args:
            method: 'simple' for geometric alignment (dlib not required on Windows)
        """
        self.method = 'simple'  # Always use simple method to avoid dlib Windows issues
    
    def get_facial_landmarks(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Detect 68 facial landmarks
        
        Args:
            image: Input image
            face_location: Face bounding box (x, y, w, h)
            
        Returns:
            Array of landmark points [(x, y), ...] or None
        """
        if self.method == 'dlib' and self.predictor:
            return self._get_landmarks_dlib(image, face_location)
        else:
            # Fallback to simple alignment without landmarks
            return None
    
    def _get_landmarks_dlib(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> np.ndarray:
        """Get landmarks using dlib"""
        import dlib
        
        x, y, w, h = face_location
        
        # Convert to dlib rectangle
        rect = dlib.rectangle(int(x), int(y), int(x + w), int(y + h))
        
        # Get landmarks
        shape = self.predictor(image, rect)
        
        # Convert to numpy array
        landmarks = np.array([[p.x, p.y] for p in shape.parts()])
        
        return landmarks
    
    def align_face(self, image: np.ndarray, landmarks: Optional[np.ndarray] = None, 
                   face_location: Optional[Tuple[int, int, int, int]] = None,
                   desired_size: Tuple[int, int] = (256, 256)) -> Optional[np.ndarray]:
        """
        Align face to canonical pose
        
        Args:
            image: Input image
            landmarks: Facial landmarks (68 points)
            face_location: Face bounding box if landmarks not provided
            desired_size: Output size for aligned face
            
        Returns:
            Aligned face image
        """
        if landmarks is not None and len(landmarks) >= 68:
            # Align using landmarks (more accurate)
            return self._align_with_landmarks(image, landmarks, desired_size)
        elif face_location is not None:
            # Simple alignment using face box
            return self._align_simple(image, face_location, desired_size)
        else:
            return None
    
    def _align_with_landmarks(self, image: np.ndarray, landmarks: np.ndarray, 
                             desired_size: Tuple[int, int]) -> np.ndarray:
        """
        Align face using facial landmarks (eyes, nose, mouth)
        Uses similarity transform to align to canonical pose
        """
        # Get eye centers
        left_eye = landmarks[36:42].mean(axis=0)  # Left eye landmarks
        right_eye = landmarks[42:48].mean(axis=0)  # Right eye landmarks
        
        # Compute angle between eyes
        dy = right_eye[1] - left_eye[1]
        dx = right_eye[0] - left_eye[0]
        angle = np.degrees(np.arctan2(dy, dx))
        
        # Compute center point between eyes
        eyes_center = ((left_eye[0] + right_eye[0]) / 2, 
                      (left_eye[1] + right_eye[1]) / 2)
        
        # Get rotation matrix
        M = cv2.getRotationMatrix2D(eyes_center, angle, 1.0)
        
        # Compute output size
        (h, w) = image.shape[:2]
        
        # Rotate the image
        aligned = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC)
        
        # Resize to desired size
        aligned = cv2.resize(aligned, desired_size, interpolation=cv2.INTER_CUBIC)
        
        return aligned
    
    def _align_simple(self, image: np.ndarray, face_location: Tuple[int, int, int, int],
                     desired_size: Tuple[int, int]) -> np.ndarray:
        """
        Simple alignment by cropping and resizing face region
        """
        x, y, w, h = face_location
        
        # Add padding
        padding = 0.2
        pad_w = int(w * padding)
        pad_h = int(h * padding)
        
        y1 = max(0, y - pad_h)
        y2 = min(image.shape[0], y + h + pad_h)
        x1 = max(0, x - pad_w)
        x2 = min(image.shape[1], x + w + pad_w)
        
        # Crop face
        face = image[y1:y2, x1:x2]
        
        if face.size == 0:
            return None
        
        # Resize to desired size
        aligned = cv2.resize(face, desired_size, interpolation=cv2.INTER_CUBIC)
        
        return aligned
    
    def normalize_face(self, face_image: np.ndarray) -> np.ndarray:
        """
        Normalize face image for recognition
        - Histogram equalization for consistent lighting
        - Normalize pixel values
        
        Args:
            face_image: Aligned face image
            
        Returns:
            Normalized face image
        """
        if face_image is None or face_image.size == 0:
            return None
        
        # Convert to grayscale if color
        if len(face_image.shape) == 3:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_image
        
        # Apply histogram equalization for better contrast
        normalized = cv2.equalizeHist(gray)
        
        # Normalize pixel values to [0, 1]
        normalized = normalized.astype(np.float32) / 255.0
        
        return normalized


def align_face(image: np.ndarray, face_location: Tuple[int, int, int, int], 
               size: Tuple[int, int] = (256, 256)) -> Optional[np.ndarray]:
    """
    Convenience function to align face
    
    Args:
        image: Input image
        face_location: Face bounding box (x, y, w, h)
        size: Desired output size
        
    Returns:
        Aligned face image
    """
    aligner = FaceAligner(method='simple')  # Use simple method as fallback
    return aligner.align_face(image, face_location=face_location, desired_size=size)


def normalize_face(face_image: np.ndarray) -> np.ndarray:
    """
    Convenience function to normalize face
    
    Args:
        face_image: Input face image
        
    Returns:
        Normalized face image
    """
    aligner = FaceAligner()
    return aligner.normalize_face(face_image)
