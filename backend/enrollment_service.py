"""
Enhanced Enrollment System
Processes multiple frames to extract high-quality face embeddings
"""
import cv2
import numpy as np
import base64
from typing import List, Dict, Optional
import sys
import os

# Add ml_cvs to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ml_cvs'))

from ml_cvs.face_engine import FaceEngine
from ml_cvs.quality import check_quality_gates, filter_quality_frames, preprocess_face
from ml_cvs.config import ENROLLMENT_FRAMES_MIN, ENROLLMENT_FRAMES_MAX


def decode_base64_image(base64_string: str) -> Optional[np.ndarray]:
    """
    Decode base64 image string to numpy array
    
    Args:
        base64_string: Base64 encoded image (with or without data URI prefix)
        
    Returns:
        Image as numpy array (BGR format) or None
    """
    try:
        # Remove data URI prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        img_bytes = base64.b64decode(base64_string)
        
        # Convert to numpy array
        nparr = np.frombuffer(img_bytes, np.uint8)
        
        # Decode image
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return image
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        return None


def process_enrollment_frames(frames_b64: List[str], max_embeddings: int = ENROLLMENT_FRAMES_MAX,
                              face_engine: FaceEngine = None) -> Dict:
    """
    Process multiple enrollment frames and extract best quality embeddings
    
    Args:
        frames_b64: List of base64 encoded images
        max_embeddings: Maximum number of embeddings to keep
        face_engine: FaceEngine instance (creates new if None)
        
    Returns:
        Dict with:
            - success: bool
            - embeddings: List of embedding bytes
            - quality_scores: List of quality scores
            - message: str
            - total_frames: int
            - valid_frames: int
    """
    result = {
        'success': False,
        'embeddings': [],
        'quality_scores': [],
        'message': None,
        'total_frames': len(frames_b64),
        'valid_frames': 0
    }
    
    if not frames_b64:
        result['message'] = 'No frames provided'
        return result
    
    # Initialize face engine if not provided
    if face_engine is None:
        face_engine = FaceEngine()
    
    # Decode all frames
    frames = []
    for i, frame_b64 in enumerate(frames_b64):
        frame = decode_base64_image(frame_b64)
        if frame is not None:
            frames.append(frame)
    
    if not frames:
        result['message'] = 'No valid frames could be decoded'
        return result
    
    # Detect faces and extract embeddings with quality checks
    candidates = []
    
    for frame in frames:
        # Detect faces
        detected_faces = face_engine.detect_faces(frame)
        
        if not detected_faces:
            continue  # No face in this frame
        
        if len(detected_faces) > 1:
            continue  # Multiple faces - skip for enrollment
        
        # Get the single detected face
        face_data = detected_faces[0]
        bbox = face_data['bbox']
        landmarks = face_data['kps']
        det_score = face_data['det_score']
        embedding = face_data['embedding']
        
        # Extract face crop for quality check
        from ml_cvs.face_engine import extract_crop_from_bbox
        face_crop = extract_crop_from_bbox(frame, bbox)
        
        if face_crop is None:
            continue
        
        # Run quality gates
        quality = check_quality_gates(face_crop, landmarks)
        
        if not quality['passed']:
            continue  # Failed quality check
        
        # Calculate composite quality score
        quality_score = (
            det_score * 0.5 +  # Detection confidence
            min(quality['blur_score'] / 200, 1.0) * 0.3 +  # Sharpness (normalized)
            (1.0 - abs(quality['angles']['yaw']) / 30 if quality['angles'] else 0.5) * 0.2  # Angle
        )
        
        candidates.append({
            'embedding': embedding,
            'quality_score': quality_score,
            'face_crop': face_crop
        })
    
    result['valid_frames'] = len(candidates)
    
    if not candidates:
        result['message'] = 'No high-quality faces found in provided frames'
        return result
    
    if len(candidates) < ENROLLMENT_FRAMES_MIN:
        result['message'] = f'Not enough quality frames ({len(candidates)} < {ENROLLMENT_FRAMES_MIN} minimum)'
        return result
    
    # Sort by quality score (best first)
    candidates.sort(key=lambda x: x['quality_score'], reverse=True)
    
    # Keep top N
    top_candidates = candidates[:max_embeddings]
    
    # Serialize embeddings
    import pickle
    serialized_embeddings = []
    quality_scores = []
    
    for candidate in top_candidates:
        serialized_embeddings.append(pickle.dumps(candidate['embedding']))
        quality_scores.append(candidate['quality_score'])
    
    result['success'] = True
    result['embeddings'] = serialized_embeddings
    result['quality_scores'] = quality_scores
    result['message'] = f'Successfully extracted {len(serialized_embeddings)} high-quality embeddings'
    
    return result


def process_single_registration_image(image: np.ndarray, face_engine: FaceEngine = None) -> Dict:
    """
    Process single image for backwards compatibility with existing registration
    
    Args:
        image: Input image (BGR format)
        face_engine: FaceEngine instance (creates new if None)
        
    Returns:
        Dict with success, embedding, message
    """
    result = {
        'success': False,
        'embedding': None,
        'message': None
    }
    
    if image is None or image.size == 0:
        result['message'] = 'Invalid image'
        return result
    
    # Initialize face engine if not provided
    if face_engine is None:
        face_engine = FaceEngine()
    
    # Detect faces
    faces = face_engine.detect_faces(image)
    
    if not faces:
        result['message'] = 'No face detected in image'
        return result
    
    if len(faces) > 1:
        result['message'] = 'Multiple faces detected. Please provide image with single face'
        return result
    
    face_data = faces[0]
    bbox = face_data['bbox']
    landmarks = face_data['kps']
    embedding = face_data['embedding']
    
    # Extract and check quality
    from ml_cvs.face_engine import extract_crop_from_bbox
    face_crop = extract_crop_from_bbox(image, bbox)
    
    quality = check_quality_gates(face_crop, landmarks)
    
    if not quality['passed']:
        result['message'] = quality.get('reason', 'Poor image quality')
        return result
    
    # Serialize embedding
    import pickle
    embedding_bytes = pickle.dumps(embedding)
    
    result['success'] = True
    result['embedding'] = embedding_bytes
    result['message'] = 'Face processed successfully'
    
    return result
