"""
Quality Gates and Preprocessing for Face Recognition
Implements checks for face size, blur, angle, and CLAHE preprocessing
"""
import cv2
import numpy as np
from typing import Dict, Optional, Tuple

# Quality gate thresholds (configurable)
MIN_FACE_SIZE = 80  # Minimum width/height in pixels
BLUR_THRESHOLD = 100.0  # Laplacian variance threshold
YAW_MAX = 25  # Max yaw angle (degrees)
PITCH_MAX = 20  # Max pitch angle (degrees)
ROLL_MAX = 30  # Max roll angle (degrees)

# CLAHE parameters
CLAHE_CLIP_LIMIT = 2.0
CLAHE_GRID_SIZE = (8, 8)
USE_CLAHE = True


def is_face_too_small(crop: np.ndarray, min_size: int = MIN_FACE_SIZE) -> bool:
    """
    Check if face crop is too small
    
    Args:
        crop: Face image crop
        min_size: Minimum width/height threshold
        
    Returns:
        True if face is too small
    """
    if crop is None or crop.size == 0:
        return True
    
    height, width = crop.shape[:2]
    return width < min_size or height < min_size


def calculate_blur_score(image: np.ndarray) -> float:
    """
    Calculate blur score using variance of Laplacian
    
    Args:
        image: Input image (grayscale or color)
        
    Returns:
        Blur score (higher = sharper)
    """
    if image is None or image.size == 0:
        return 0.0
    
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Calculate Laplacian variance
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    return float(lap_var)


def is_blurry(image: np.ndarray, threshold: float = BLUR_THRESHOLD) -> bool:
    """
    Check if image is too blurry
    
    Args:
        image: Input image
        threshold: Blur threshold (lower values = stricter)
        
    Returns:
        True if image is blurry
    """
    blur_score = calculate_blur_score(image)
    return blur_score < threshold


def estimate_head_pose(landmarks: np.ndarray) -> Dict[str, float]:
    """
    Estimate head pose angles from 5-point facial landmarks
    Uses simplified approximation (not full 3D pose estimation)
    
    Args:
        landmarks: 5-point landmarks array [[left_eye], [right_eye], [nose], [left_mouth], [right_mouth]]
                  Shape: (5, 2) or list of 5 points
        
    Returns:
        Dict with 'yaw', 'pitch', 'roll' in degrees (approximate)
    """
    if landmarks is None or len(landmarks) < 5:
        return {'yaw': 0.0, 'pitch': 0.0, 'roll': 0.0}
    
    # Extract key points
    left_eye = np.array(landmarks[0][:2])
    right_eye = np.array(landmarks[1][:2])
    nose = np.array(landmarks[2][:2])
    left_mouth = np.array(landmarks[3][:2])
    right_mouth = np.array(landmarks[4][:2])
    
    # Calculate eye center and mouth center
    eye_center = (left_eye + right_eye) / 2
    mouth_center = (left_mouth + right_mouth) / 2
    
    # Roll: angle between eyes
    eye_delta = right_eye - left_eye
    roll = np.degrees(np.arctan2(eye_delta[1], eye_delta[0]))
    
    # Yaw (left-right): based on eye-nose-mouth horizontal alignment
    # If nose is significantly left/right of eye-mouth centerline, face is turned
    face_centerline_x = eye_center[0]
    nose_offset = nose[0] - face_centerline_x
    eye_distance = np.linalg.norm(right_eye - left_eye)
    
    # Normalize by face width
    yaw_ratio = nose_offset / (eye_distance + 1e-6)
    yaw = yaw_ratio * 30  # Rough scaling (adjust empirically)
    
    # Pitch (up-down): based on eye-mouth vertical distance
    eye_mouth_dist = np.linalg.norm(mouth_center - eye_center)
    expected_dist = eye_distance * 1.1  # Rough ratio for frontal face
    
    pitch_ratio = (eye_mouth_dist - expected_dist) / (expected_dist + 1e-6)
    pitch = pitch_ratio * 20  # Rough scaling
    
    return {
        'yaw': float(yaw),
        'pitch': float(pitch),
        'roll': float(roll)
    }


def is_bad_angle(landmarks: np.ndarray, yaw_max: float = YAW_MAX, 
                 pitch_max: float = PITCH_MAX, roll_max: float = ROLL_MAX) -> bool:
    """
    Check if head pose angle exceeds limits
    
    Args:
        landmarks: 5-point facial landmarks
        yaw_max: Max yaw angle (degrees)
        pitch_max: Max pitch angle (degrees)
        roll_max: Max roll angle (degrees)
        
    Returns:
        True if any angle exceeds limits
    """
    pose = estimate_head_pose(landmarks)
    
    return (abs(pose['yaw']) > yaw_max or 
            abs(pose['pitch']) > pitch_max or 
            abs(pose['roll']) > roll_max)


def apply_clahe(image: np.ndarray, clip_limit: float = CLAHE_CLIP_LIMIT, 
                grid_size: Tuple[int, int] = CLAHE_GRID_SIZE) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) for lighting normalization
    
    Args:
        image: Input image (BGR or grayscale)
        clip_limit: Clipping limit (higher = more contrast)
        grid_size: Grid size for local histogram equalization
        
    Returns:
        CLAHE-enhanced image
    """
    if image is None or image.size == 0:
        return image
    
    # Convert to LAB color space for better lighting normalization
    if len(image.shape) == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
    else:
        l = image
    
    # Apply CLAHE to L channel (lightness)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
    l_clahe = clahe.apply(l)
    
    # Merge back if color image
    if len(image.shape) == 3:
        lab_clahe = cv2.merge([l_clahe, a, b])
        enhanced = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
    else:
        enhanced = l_clahe
    
    return enhanced


def preprocess_face(crop: np.ndarray, apply_clahe_flag: bool = USE_CLAHE) -> np.ndarray:
    """
    Apply all preprocessing steps to face crop
    
    Args:
        crop: Face image crop
        apply_clahe_flag: Whether to apply CLAHE
        
    Returns:
        Preprocessed face image
    """
    if crop is None or crop.size == 0:
        return crop
    
    processed = crop.copy()
    
    # Apply CLAHE for lighting normalization
    if apply_clahe_flag:
        processed = apply_clahe(processed)
    
    return processed


def check_quality_gates(face_crop: np.ndarray, landmarks: Optional[np.ndarray] = None) -> Dict:
    """
    Run all quality gates on a face crop
    
    Args:
        face_crop: Face image crop
        landmarks: Optional 5-point landmarks for angle check
        
    Returns:
        Dict with:
            - passed: bool (True if all gates passed)
            - reason: str (rejection reason if failed)
            - blur_score: float
            - size: tuple (width, height)
            - angles: dict (if landmarks provided)
    """
    result = {
        'passed': True,
        'reason': None,
        'blur_score': 0.0,
        'size': (0, 0),
        'angles': None
    }
    
    if face_crop is None or face_crop.size == 0:
        result['passed'] = False
        result['reason'] = 'Empty image'
        return result
    
    # Size check
    height, width = face_crop.shape[:2]
    result['size'] = (width, height)
    
    if is_face_too_small(face_crop):
        result['passed'] = False
        result['reason'] = f'Face too small ({width}x{height} < {MIN_FACE_SIZE}px)'
        return result
    
    # Blur check
    blur_score = calculate_blur_score(face_crop)
    result['blur_score'] = blur_score
    
    if is_blurry(face_crop):
        result['passed'] = False
        result['reason'] = f'Image too blurry (score: {blur_score:.1f} < {BLUR_THRESHOLD})'
        return result
    
    # Angle check (if landmarks provided)
    if landmarks is not None:
        angles = estimate_head_pose(landmarks)
        result['angles'] = angles
        
        if is_bad_angle(landmarks):
            result['passed'] = False
            result['reason'] = f'Bad angle (yaw: {angles["yaw"]:.1f}°, pitch: {angles["pitch"]:.1f}°)'
            return result
    
    result['reason'] = 'All quality gates passed'
    return result


# Convenience functions
def filter_quality_frames(frames_with_landmarks: list) -> list:
    """
    Filter list of (frame, landmarks) tuples by quality gates
    
    Args:
        frames_with_landmarks: List of (frame, landmarks, det_score) tuples
        
    Returns:
        Filtered list with only high-quality frames
    """
    passed = []
    
    for frame, landmarks, det_score in frames_with_landmarks:
        quality = check_quality_gates(frame, landmarks)
        
        if quality['passed']:
            # Add quality score for sorting
            quality_score = (
                det_score * 0.5 +  # Detection confidence
                min(quality['blur_score'] / 200, 1.0) * 0.3 +  # Sharpness (normalized)
                (1.0 - abs(quality['angles']['yaw']) / 30 if quality['angles'] else 0.5) * 0.2
            )
            passed.append((frame, landmarks, quality_score))
    
    # Sort by quality score (best first)
    passed.sort(key=lambda x: x[2], reverse=True)
    
    return passed
