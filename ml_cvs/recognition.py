"""
Face Recognition Module
Main recognition pipeline implementing SRDS specification:
1. Detect face → 2. Align face → 3. Extract embedding → 4. Match → 5. Return result
"""
import cv2
import numpy as np
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta

from .face_detection import FaceDetector
from .face_alignment import FaceAligner
from .embedding_extractor import EmbeddingExtractor


class FaceRecognizer:
    """Complete face recognition pipeline"""
    
    def __init__(self, confidence_threshold: float = 0.6, duplicate_threshold_seconds: int = 5):
        """
        Initialize face recognizer
        
        Args:
            confidence_threshold: Minimum confidence for recognition (0-1)
            duplicate_threshold_seconds: Prevent duplicate detections within this time
        """
        self.detector = FaceDetector()
        self.aligner = FaceAligner(method='simple')
        self.extractor = EmbeddingExtractor()
        self.confidence_threshold = confidence_threshold
        self.duplicate_threshold = duplicate_threshold_seconds
        
        # Track recent detections to prevent duplicates
        self.recent_detections = {}  # {student_id: timestamp}
    
    def recognize_face(self, frame: np.ndarray, known_embeddings: List[Tuple[int, str, bytes]]) -> Dict:
        """
        Main recognition pipeline
        
        Args:
            frame: Input image/frame
            known_embeddings: List of (student_id, name, embedding_bytes) from database
            
        Returns:
            Recognition result dictionary
        """
        result = {
            'recognized': False,
            'student_id': None,
            'student_name': None,
            'confidence': 0.0,
            'face_location': None,
            'message': None
        }
        
        if frame is None or frame.size == 0:
            result['message'] = 'Invalid frame'
            return result
        
        # Step 1: Detect faces
        faces = self.detector.detect_faces(frame)
        
        if not faces:
            result['message'] = 'No face detected'
            return result
        
        if len(faces) > 1:
            result['message'] = f'Multiple faces detected ({len(faces)}), using first'
        
        # Use first detected face
        face_location = faces[0]
        result['face_location'] = {
            'x': int(face_location[0]),
            'y': int(face_location[1]),
            'width': int(face_location[2]),
            'height': int(face_location[3])
        }
        
        # Step 2: Extract and align face
        face_image = self.detector.extract_face_region(frame, face_location)
        
        if face_image is None:
            result['message'] = 'Failed to extract face region'
            return result
        
        # Check image quality
        quality = self.detector.check_image_quality(face_image)
        if not quality['valid']:
            result['message'] = quality.get('reason', 'Poor image quality')
            return result
        
        # Align face
        aligned_face = self.aligner.align_face(frame, face_location=face_location, desired_size=(256, 256))
        
        if aligned_face is None:
            aligned_face = face_image  # Use unaligned if alignment fails
        
        # Step 3: Extract embedding
        query_embedding = self.extractor.extract_embedding(aligned_face)
        
        if query_embedding is None:
            result['message'] = 'Failed to extract face features'
            return result
        
        # Step 4: Match against known embeddings
        if not known_embeddings:
            result['message'] = 'No enrolled students in database'
            return result
        
        best_match = self._find_best_match(query_embedding, known_embeddings)
        
        if best_match is None:
            result['message'] = 'No match found'
            return result
        
        student_id, student_name, confidence = best_match
        
        # Step 5: Check confidence threshold
        if confidence < self.confidence_threshold:
            result['message'] = f'Low confidence ({confidence:.1%})'
            result['confidence'] = confidence * 100
            return result
        
        # Check for duplicate detection
        if self._is_duplicate_detection(student_id):
            result['message'] = f'Already marked present recently'
            result['recognized'] = False
            result['student_id'] = student_id
            result['student_name'] = student_name
            result['confidence'] = confidence * 100
            return result
        
        # Success!
        result['recognized'] = True
        result['student_id'] = student_id
        result['student_name'] = student_name
        result['confidence'] = confidence * 100
        result['message'] = 'Face recognized successfully'
        
        # Record detection
        self.recent_detections[student_id] = datetime.now()
        
        return result
    
    def _find_best_match(self, query_embedding: np.ndarray,
                        known_embeddings: List[Tuple[int, str, bytes]]) -> Optional[Tuple[int, str, float]]:
        """
        Find best matching student

        Args:
            query_embedding: Query face embedding
            known_embeddings: List of known student embeddings

        Returns:
            (student_id, name, confidence) or None
        """
        best_similarity = 0.0
        best_match = None

        for student_id, name, embedding_bytes in known_embeddings:
            # Deserialize embedding
            known_embedding = self.extractor.deserialize_embedding(embedding_bytes)

            if known_embedding is None:
                continue

            # Calculate similarity
            similarity = self.extractor.calculate_similarity(query_embedding, known_embedding)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = (student_id, name, similarity)

        return best_match
    
    def _is_duplicate_detection(self, student_id: int) -> bool:
        """
        Check if student was recently detected
        
        Args:
            student_id: Student ID to check
            
        Returns:
            True if duplicate
        """
        if student_id not in self.recent_detections:
            return False
        
        last_detection = self.recent_detections[student_id]
        time_diff = (datetime.now() - last_detection).total_seconds()
        
        return time_diff < self.duplicate_threshold
    
    def clear_recent_detections(self):
        """Clear recent detection cache"""
        self.recent_detections = {}
    
    def process_registration_image(self, image: np.ndarray) -> Dict:
        """
        Process image for student registration
        
        Args:
            image: Input image
            
        Returns:
            Dict with embedding and status
        """
        result = {
            'success': False,
            'embedding': None,
            'face_location': None,
            'message': None
        }
        
        # Detect face
        faces = self.detector.detect_faces(image)
        
        if not faces:
            result['message'] = 'No face detected in image'
            return result
        
        if len(faces) > 1:
            result['message'] = 'Multiple faces detected. Please provide image with single face'
            return result
        
        face_location = faces[0]
        
        # Check quality
        face_image = self.detector.extract_face_region(image, face_location)
        quality = self.detector.check_image_quality(face_image)
        
        if not quality['valid']:
            result['message'] = quality.get('reason', 'Poor image quality')
            return result
        
        # Align face
        aligned_face = self.aligner.align_face(image, face_location=face_location)
        
        if aligned_face is None:
            aligned_face = face_image
        
        # Extract embedding
        embedding = self.extractor.extract_embedding(aligned_face)
        
        if embedding is None:
            result['message'] = 'Failed to extract face features'
            return result
        
        # Serialize embedding
        embedding_bytes = self.extractor.serialize_embedding(embedding)
        
        result['success'] = True
        result['embedding'] = embedding_bytes
        result['face_location'] = face_location
        result['message'] = 'Face processed successfully'
        
        return result


# Convenience functions

def recognize_from_frame(frame: np.ndarray, known_embeddings: List[Tuple[int, str, bytes]], 
                        threshold: float = 0.6) -> Dict:
    """
    Recognize face in frame
    
    Args:
        frame: Input frame
        known_embeddings: Known student embeddings
        threshold: Confidence threshold
        
    Returns:
        Recognition result
    """
    recognizer = FaceRecognizer(confidence_threshold=threshold)
    return recognizer.recognize_face(frame, known_embeddings)


def process_registration(image: np.ndarray) -> Dict:
    """
    Process registration image
    
    Args:
        image: Input image
        
    Returns:
        Processing result with embedding
    """
    recognizer = FaceRecognizer()
    return recognizer.process_registration_image(image)
