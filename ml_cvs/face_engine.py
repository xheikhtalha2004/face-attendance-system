"""
Face Engine using YuNet (detection) + InsightFace ArcFace (embeddings)
YuNet provides superior face detection, ArcFace provides best-in-class embeddings
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
    Hybrid face engine:
    - YuNet for fast, accurate face detection
    - InsightFace ArcFace for high-quality embeddings
    """
    
    def __init__(self, model_name='buffalo_l', ctx_id=-1):
        """
        Initialize Face Engine with YuNet detection + InsightFace embeddings
        
        Args:
            model_name: InsightFace model for embeddings ('buffalo_l' recommended)
            ctx_id: Device ID (-1 for CPU, 0+ for GPU)
        """
        self.model_name = model_name
        self.ctx_id = ctx_id
        
        print(f"Initializing Face Engine...")
        print(f"  Detection: YuNet (DNN)")
        print(f"  Embeddings: InsightFace ArcFace ({model_name})")
        
        # Initialize YuNet detector
        try:
            from ml_cvs.face_detection import FaceDetector
            from ml_cvs.config import YUNET_SCORE_THRESHOLD, MIN_FACE_SIZE
            
            self.yunet_detector = FaceDetector(
                min_face_size=MIN_FACE_SIZE,
                score_threshold=YUNET_SCORE_THRESHOLD
            )
            print(f"  [OK] YuNet detector initialized")
        except Exception as e:
            print(f"  [ERROR] YuNet initialization failed: {e}")
            raise

        # Initialize InsightFace for embeddings
        try:
            self.app = FaceAnalysis(name=model_name)
            self.app.prepare(ctx_id=ctx_id, det_size=(640, 640))

            print(f"  [OK] InsightFace initialized ({model_name})")
            print(f"  [OK] Using {'GPU' if ctx_id >= 0 else 'CPU'}")
        except Exception as e:
            print(f"  [ERROR] Error initializing InsightFace: {str(e)}")
            raise
        
        print("[OK] Face Engine ready")
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect faces in frame using YuNet, then extract embeddings with InsightFace
        
        Args:
            frame: Input image (BGR format from OpenCV)
            
        Returns:
            List of face dictionaries with:
                - bbox: (x, y, w, h) bounding box
                - kps: None (YuNet doesn't provide landmarks in standard way)
                - det_score: detection confidence (0-1)
                - embedding: 512D ArcFace embedding
        """
        if frame is None or frame.size == 0:
            return []
        
        # Detect faces with YuNet
        face_bboxes = self.yunet_detector.detect_faces(frame)
        
        if not face_bboxes:
            return []
        
        # Extract embeddings for each detected face
        result = []
        for bbox in face_bboxes:
            x, y, w, h = bbox
            
            # Extract face crop with padding
            face_crop = extract_crop_from_bbox(frame, bbox, padding=0.2)
            if face_crop is None:
                continue
            
            # Get embedding from InsightFace
            embedding = self._extract_embedding_from_crop(face_crop)
            if embedding is None:
                continue
            
            face_dict = {
                'bbox': (x, y, w, h),
                'kps': None,
                'det_score': 0.95,
                'embedding': embedding
            }
            
            result.append(face_dict)
        
        return result
    
    
    def _extract_embedding_from_crop(self, face_crop: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract ArcFace embedding from face crop using InsightFace
        """
        if face_crop is None or face_crop.size == 0:
            return None
        
        # Convert BGR to RGB
        rgb_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        
        # Get embedding using InsightFace
        faces = self.app.get(rgb_crop)
        
        if not faces:
            return None
        
        # Return embedding of first (should be only) face
        return faces[0].embedding
    
    def get_embedding(self, face_crop: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract ArcFace embedding from face crop
        
        Args:
            face_crop: Cropped face image (BGR format)
            
        Returns:
            512D normalized embedding vector or None if no face detected
        """
        return self._extract_embedding_from_crop(face_crop)
    
    def compare_embeddings_cosine(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compare two embeddings using cosine similarity
        
        Args:
            emb1: First embedding (512D)
            emb2: Second embedding (512D)
            
        Returns:
            Cosine similarity (0-1, higher = more similar)
        """
        if emb1 is None or emb2 is None:
            return 0.0
        
        # Ensure numpy arrays
        emb1 = np.asarray(emb1, dtype=np.float32)
        emb2 = np.asarray(emb2, dtype=np.float32)
        
        # Compute L2 norms
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Cosine similarity: dot(u, v) / (norm(u) * norm(v))
        similarity = np.dot(emb1, emb2) / (norm1 * norm2)
        
        # Clamp to [0, 1] range
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
    """
    Create and return FaceEngine instance
    
    Args:
        model_name: InsightFace model name
        use_gpu: Use GPU for processing (True for GPU, False for CPU)
    """
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
