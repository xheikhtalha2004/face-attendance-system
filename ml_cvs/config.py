"""
Configuration file for Face Attendance System
Centralized configuration for all ML/CV parameters
"""

# ============================================================================
# InsightFace Model Configuration
# ============================================================================
INSIGHTFACE_MODEL = 'buffalo_l'  # 'buffalo_l' (best accuracy) or 'buffalo_sc' (faster)
USE_GPU = False  # Set True to use CUDA GPU (requires onnxruntime-gpu)

# ============================================================================
# Face Detection (YuNet)
# ============================================================================
MIN_FACE_SIZE = 80  # Minimum face width/height in pixels
YUNET_SCORE_THRESHOLD = 0.9  # Detection confidence threshold (0-1, higher = stricter)
YUNET_NMS_THRESHOLD = 0.3    # Non-maximum suppression (0-1, lower = fewer overlaps)
YUNET_TOP_K = 5000           # Max detections before NMS
YUNET_MODEL_PATH = None      # Auto-download to ml_cvs/models/ if None

# ============================================================================
# Quality Gates
# ============================================================================
BLUR_THRESHOLD = 100.0  # Laplacian variance threshold (80-150 typical range)
YAW_MAX = 25  # Max yaw angle (degrees, left-right turn)
PITCH_MAX = 20  # Max pitch angle (degrees, up-down tilt)
ROLL_MAX = 30  # Max roll angle (degrees, head tilt)

# ============================================================================
# Preprocessing
# ============================================================================
USE_CLAHE = True  # Apply CLAHE lighting normalization
CLAHE_CLIP_LIMIT = 2.0  # CLAHE clipping limit
CLAHE_GRID_SIZE = (8, 8)  # CLAHE grid size

# ============================================================================
# Face Recognition (ArcFace)
# ============================================================================
SIMILARITY_METRIC = 'cosine'  # 'cosine' for ArcFace (normalized embeddings)
SIMILARITY_THRESHOLD = 0.35  # Cosine similarity threshold (0.30-0.45 range)
                             # Lower = stricter matching
                             # Higher = more lenient matching

# ============================================================================
# Attendance Cooldown
# ============================================================================
COOLDOWN_SECONDS = 120  # Cooldown period after attendance marked (2 minutes)

# ============================================================================
# Enrollment
# ============================================================================
ENROLLMENT_FRAMES_MIN = 5  # Minimum frames to keep for enrollment
ENROLLMENT_FRAMES_MAX = 15  # Maximum frames to keep for enrollment
ENROLLMENT_CAPTURE_INTERVAL_MS = 200  # Interval between frame captures (ms)

# ============================================================================
# Performance
# ============================================================================
TARGET_FPS = 10  # Target frame processing rate for recognition
FRAME_SKIP = 3  # Process every Nth frame (1 = process all frames)

# ============================================================================
# Timetable/Schedule
# ============================================================================
SLOT_TIMES = {
    1: {'start': '08:30', 'end': '09:50'},  # Slot 1: 80 minutes
    2: {'start': '09:50', 'end': '11:10'},  # Slot 2: 80 minutes
    3: {'start': '11:10', 'end': '12:30'},  # Slot 3: 80 minutes
    # Break: 12:30 - 13:30 (60 minutes)
    4: {'start': '13:30', 'end': '14:50'},  # Slot 4: 80 minutes
    5: {'start': '14:50', 'end': '16:10'},  # Slot 5: 80 minutes
}

BREAK_TIME = {'start': '12:30', 'end': '13:30'}
DEFAULT_LATE_THRESHOLD_MINUTES = 5  # Default late arrival threshold


# ============================================================================
# Auto-Session Service
# ============================================================================
SESSION_CHECK_INTERVAL_MINUTES = 1  # Check for new sessions every minute
AUTO_MARK_ABSENTEES = True  # Automatically mark absent students
ABSENTEE_MARK_DELAY_MINUTES = 5  # Delay before marking absentees (after late threshold)
