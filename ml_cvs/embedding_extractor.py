"""
Embedding Extractor Module
Extract face embeddings using FaceNet/ArcFace approach (per SRDS specification)
Option C: Uses face_recognition library (128D embeddings) for faster implementation
Can be upgraded to custom FaceNet/ArcFace later
"""
import numpy as np
import cv2
from typing import List, Optional, Tuple
import pickle


class EmbeddingExtractor:
    """Extract face embeddings for recognition"""
    
    def __init__(self, model_type='facenet'):
        """
        Initialize embedding extractor
        
        Args:
            model_type: 'facenet' (using face_recognition library) or 'arcface' (custom)
        """
        self.model_type = model_type
        self.embedding_size = 128  # Standard FaceNet embedding size
        
        # Load model
        try:
            import face_recognition
            self.model = 'face_recognition'
            print("[OK] Using face_recognition library for embeddings")
        except ImportError:
            print("Warning: face_recognition not available")
            self.model = None
    
    def extract_embedding(self, face_image: np.ndarray, aligned: bool = False) -> Optional[np.ndarray]:
        """
        Extract 128-dimensional face embedding
        
        Args:
            face_image: Input face image (RGB format)
            aligned: Whether face is already aligned
            
        Returns:
            128D embedding vector or None
        """
        if face_image is None or face_image.size == 0:
            return None
        
        if self.model == 'face_recognition':
            return self._extract_facenet(face_image)
        else:
            # Fallback to simple feature extraction
            return self._extract_simple(face_image)
    
    def _extract_facenet(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Extract embedding using face_recognition library (FaceNet-based)"""
        import face_recognition
        
        # Ensure RGB format
        if len(face_image.shape) == 2:
            # Grayscale to RGB
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_GRAY2RGB)
        elif face_image.shape[2] == 4:
            # RGBA to RGB
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGRA2RGB)
        elif len(face_image.shape) == 3 and face_image.shape[2] == 3:
            # BGR to RGB
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = face_image
        
        # Detect face locations first
        face_locations = face_recognition.face_locations(rgb_image)
        
        if not face_locations:
            # No face detected, try with the whole image
            # Resize to reasonable size
            h, w = rgb_image.shape[:2]
            if h > 500 or w > 500:
                scale = 500 / max(h, w)
                new_h, new_w = int(h * scale), int(w * scale)
                rgb_image = cv2.resize(rgb_image, (new_w, new_h))
            
            # Try again
            face_locations = face_recognition.face_locations(rgb_image)
            
            if not face_locations:
                return None
        
        # Extract encodings
        encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        if encodings:
            return encodings[0]  # Return first face encoding
        else:
            return None
    
    def _extract_simple(self, face_image: np.ndarray) -> np.ndarray:
        """Simple feature extraction fallback (not recommended for production)"""
        # Resize to fixed size
        resized = cv2.resize(face_image, (128, 128))
        
        # Convert to grayscale
        if len(resized.shape) == 3:
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        else:
            gray = resized
        
        # Flatten and normalize
        features = gray.flatten().astype(np.float32) / 255.0
        
        # Reduce dimensionality to 128
        # Use simple binning
        bin_size = len(features) // 128
        embedding = np.array([features[i*bin_size:(i+1)*bin_size].mean() 
                            for i in range(128)])
        
        return embedding
    
    def batch_extract(self, face_images: List[np.ndarray]) -> List[Optional[np.ndarray]]:
        """
        Extract embeddings for multiple faces
        
        Args:
            face_images: List of face images
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for face_image in face_images:
            embedding = self.extract_embedding(face_image)
            embeddings.append(embedding)
        
        return embeddings
    
    def serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """
        Serialize embedding for database storage
        
        Args:
            embedding: Numpy array embedding
            
        Returns:
            Serialized bytes
        """
        if embedding is None:
            return None
        
        return pickle.dumps(embedding)
    
    def deserialize_embedding(self, embedding_bytes: bytes) -> np.ndarray:
        """
        Deserialize embedding from database
        
        Args:
            embedding_bytes: Serialized embedding
            
        Returns:
            Numpy array embedding
        """
        if embedding_bytes is None:
            return None
        
        return pickle.loads(embedding_bytes)
    
    def compare_embeddings(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compare two embeddings using Euclidean distance
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Distance (lower = more similar)
        """
        if embedding1 is None or embedding2 is None:
            return float('inf')
        
        # Euclidean distance
        distance = np.linalg.norm(embedding1 - embedding2)
        
        return float(distance)
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate similarity score (0-1, higher = more similar)
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score (0-1)
        """
        distance = self.compare_embeddings(embedding1, embedding2)
        
        # Convert distance to similarity (0-1 scale)
        # Typical face_recognition distance threshold is 0.6
        # Map [0, 1.2] to [1, 0]
        similarity = max(0, 1.0 - (distance / 1.2))
        
        return similarity


# Convenience functions

def extract_embedding(face_image: np.ndarray) -> Optional[np.ndarray]:
    """
    Extract face embedding from image
    
    Args:
        face_image: Input face image
        
    Returns:
        128D embedding vector
    """
    extractor = EmbeddingExtractor()
    return extractor.extract_embedding(face_image)


def extract_embeddings_batch(face_images: List[np.ndarray]) -> List[Optional[np.ndarray]]:
    """
    Extract embeddings for multiple faces
    
    Args:
        face_images: List of face images
        
    Returns:
        List of embeddings
    """
    extractor = EmbeddingExtractor()
    return extractor.batch_extract(face_images)


def compare_faces(embedding1: np.ndarray, embedding2: np.ndarray, threshold: float = 0.6) -> bool:
    """
    Compare two face embeddings
    
    Args:
        embedding1: First embedding
        embedding2: Second embedding
        threshold: Distance threshold (default 0.6 for face_recognition)
        
    Returns:
        True if faces match
    """
    extractor = EmbeddingExtractor()
    distance = extractor.compare_embeddings(embedding1, embedding2)
    return distance < threshold


def face_distance_to_confidence(distance: float) -> float:
    """
    Convert face distance to confidence percentage
    
    Args:
        distance: Euclidean distance between embeddings
        
    Returns:
        Confidence score (0-100%)
    """
    if distance > 1.0:
        return 0.0
    
    # Linear mapping: distance 0 = 100%, distance 1 = 0%
    confidence = max(0.0, (1.0 - distance) * 100)
    
    return confidence
