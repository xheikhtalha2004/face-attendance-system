"""
Face Engine using InsightFace (RetinaFace + ArcFace)
Replaces previous face_recognition library with production-grade accuracy
"""
import numpy as np
import cv2
from typing import List, Dict, Optional, Tuple
import insightface
from insightface.app import FaceAnalysis

# Configuration constants
INSIGHTFACE_MODEL = 'buffalo_l'  # User selected: best accuracy (~500MB)
ARC_SIMILARITY_THRESHOLD = 0.35  # Cosine similarity threshold (0.30-0.45 range)


class FaceEngine:
    """
    Unified face detection + embedding extraction using InsightFace
    Uses RetinaFace for detection and ArcFace for embeddings
    """
    
    def __init__(self, model_name=INSIGHTFACE_MODEL, ctx_id=-1):
        """
        Initialize InsightFace app
        
        Args:
            model_name: Model to use ('buffalo_l' or 'buffalo_sc')
            ctx_id: -1 for CPU, 0 for GPU (CUDA device 0)
        """
        self.model_name = model_name
        self.ctx_id = ctx_id
        
        print(f"Initializing InsightFace with model: {model_name}...")
        
        # Initialize FaceAnalysis app (bundles RetinaFace + ArcFace)
        self.app = FaceAnalysis(name=model_name)
        self.app.prepare(ctx_id=ctx_id, det_size=(640, 640))
        
        print("✓ InsightFace initialized successfully")
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect faces in frame using RetinaFace
        
        Args:
            frame: Input image (BGR format from OpenCV)
            
        Returns:
            List of face dictionaries with:
                - bbox: (x, y, w, h) bounding box
                - kps: 5-point facial landmarks 
                - det_score: detection confidence (0-1)
                - embedding: 512D ArcFace embedding (if extracted)
        """
        if frame is None or frame.size == 0:
            return []
        
        # Convert BGR to RGB (InsightFace expects RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect and analyze faces
        faces = self.app.get(rgb_frame)
        
        # Convert to our format
        result = []
        for face in faces:
            # Convert bbox from (left, top, right, bottom) to (x, y, w, h)
            left, top, right, bottom = face.bbox.astype(int)
            x, y = left, top
            w, h = right - left, bottom - top
            
            face_dict = {
                'bbox': (x, y, w, h),
                'kps': face.kps,  # 5-point landmarks: [[left_eye], [right_eye], [nose], [left_mouth], [right_mouth]]
                'det_score': float(face.det_score),  # Detection confidence
                'embedding': face.embedding  # 512D normalized embedding
            }
            
            result.append(face_dict)
        
        return result
    
    def get_embedding(self, face_crop: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract ArcFace embedding from face crop
        
        Args:
            face_crop: Cropped face image (BGR format)
            
        Returns:
            512D normalized embedding vector or None if no face detected
        """
        if face_crop is None or face_crop.size == 0:
            return None
        
        # Detect face in crop
        faces = self.detect_faces(face_crop)
        
        if not faces:
            return None
        
        # Return embedding of first (largest) face
        return faces[0]['embedding']
    
    def compare_embeddings_cosine(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compare two embeddings using cosine similarity
        
        Args:
            emb1: First embedding (512D)
            emb2: Second embedding (512D)
            
        Returns:
            Cosine similarity (0-1, higher = more similar)
            ArcFace embeddings are already normalized, so this is just dot product
        """
        if emb1 is None or emb2 is None:
            return 0.0
        
        # Cosine similarity (embeddings are already L2-normalized)
        similarity = np.dot(emb1, emb2)
        
        # Clamp to [0, 1] range (should already be, but just in case)
        similarity = np.clip(similarity, 0.0, 1.0)
        
        return float(similarity)
    
    def find_best_match(self, query_embedding: np.ndarray, 
                        known_embeddings: List[Tuple[int, str, List[np.ndarray]]],
                        threshold: float = ARC_SIMILARITY_THRESHOLD) -> Optional[Tuple[int, str, float]]:
        """
        Find best match for query embedding against known students
        
        Args:
            query_embedding: Query face embedding
            known_embeddings: List of (student_id, student_name, [embeddings_list])
            threshold: Minimum similarity threshold
            
        Returns:
            (student_id, student_name, similarity) or None if no match
        """
        best_student_id = None
        best_student_name = None
        best_similarity = 0.0
        
        for student_id, student_name, student_embeddings in known_embeddings:
            # Compare against all embeddings for this student
            similarities = [
                self.compare_embeddings_cosine(query_embedding, known_emb)
                for known_emb in student_embeddings
            ]
            
            # Take best match (max similarity)
            max_sim = max(similarities) if similarities else 0.0
            
            if max_sim > best_similarity:
                best_similarity = max_sim
                best_student_id = student_id
                best_student_name = student_name
        
        # Check threshold
        if best_similarity < threshold:
            return None
        
        return (best_student_id, best_student_name, best_similarity)


# Convenience functions
def create_face_engine(model_name=INSIGHTFACE_MODEL, use_gpu=False):
    """Create and return FaceEngine instance"""
    ctx_id = 0 if use_gpu else -1
    return FaceEngine(model_name=model_name, ctx_id=ctx_id)


def extract_crop_from_bbox(frame: np.ndarray, bbox: Tuple[int, int, int, int], 
                           padding: float = 0.2) -> Optional[np.ndarray]:
    """
    Extract face crop from frame with padding
    
    Args:
        frame: Source image
        bbox: Face bounding box (x, y, w, h)
        padding: Padding ratio (0.2 = 20% padding on each side)
        
    Returns:
        Cropped face image or None
    """
    if frame is None or bbox is None:
        return None
    
    x, y, w, h = bbox
    height, width = frame.shape[:2]
    
    # Add padding
    pad_w = int(w * padding)
    pad_h = int(h * padding)
    
    # Calculate padded coordinates
    x1 = max(0, x - pad_w)
    y1 = max(0, y - pad_h)
    x2 = min(width, x + w + pad_w)
    y2 = min(height, y + h + pad_h)
    
    # Extract face
    face_crop = frame[y1:y2, x1:x2]
    
    if face_crop.size == 0:
        return None
    
    return face_crop
