"""
YuNet Model Management Utilities
Handles downloading, verification, and path management for YuNet face detection model
"""
import os
import urllib.request
import cv2
from pathlib import Path
from typing import Optional


# Model configuration
YUNET_MODEL_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
YUNET_MODEL_FILENAME = "face_detection_yunet_2023mar.onnx"
YUNET_MODEL_SIZE_EXPECTED = 385000  # Approximately 385KB


def get_models_dir() -> Path:
    """Get the models directory path, create if doesn't exist"""
    models_dir = Path(__file__).parent
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def get_yunet_model_path(auto_download: bool = True) -> Optional[str]:
    """
    Get the path to YuNet model file
    
    Args:
        auto_download: If True, download model if not found
        
    Returns:
        Absolute path to model file, or None if not found and auto_download=False
    """
    models_dir = get_models_dir()
    model_path = models_dir / YUNET_MODEL_FILENAME
    
    if model_path.exists():
        return str(model_path)
    
    if auto_download:
        print(f"YuNet model not found at {model_path}")
        print("Downloading model from OpenCV Zoo...")
        success = download_yunet_model()
        if success:
            return str(model_path)
    
    return None


def download_yunet_model(force: bool = False) -> bool:
    """
    Download YuNet model from OpenCV Zoo
    
    Args:
        force: If True, re-download even if file exists
        
    Returns:
        True if download successful, False otherwise
    """
    models_dir = get_models_dir()
    model_path = models_dir / YUNET_MODEL_FILENAME
    
    if model_path.exists() and not force:
        print(f"[OK] Model already exists at {model_path}")
        return True
    
    try:
        print(f"Downloading YuNet model from: {YUNET_MODEL_URL}")
        print(f"Destination: {model_path}")
        print("Please wait... (~385KB)")
        
        # Download with progress callback
        def progress_callback(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
        
        urllib.request.urlretrieve(YUNET_MODEL_URL, model_path, progress_callback)
        print()  # New line after progress
        
        # Verify file size
        actual_size = model_path.stat().st_size
        print(f"[OK] Download complete! File size: {actual_size} bytes")

        if actual_size < 100000:  # Less than 100KB seems wrong
            print(f"[WARN] Warning: Downloaded file seems too small ({actual_size} bytes)")
            print(f"   Expected approximately {YUNET_MODEL_SIZE_EXPECTED} bytes")
            return False

        return True

    except Exception as e:
        print(f"[ERROR] Error downloading YuNet model: {str(e)}")
        print(f"\nManual download instructions:")
        print(f"1. Download from: {YUNET_MODEL_URL}")
        print(f"2. Save to: {model_path}")
        return False


def verify_yunet_model(model_path: str) -> bool:
    """
    Verify that the YuNet model file is valid
    
    Args:
        model_path: Path to model file
        
    Returns:
        True if model is valid, False otherwise
    """
    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found: {model_path}")
        return False

    file_size = os.path.getsize(model_path)
    if file_size < 100000:
        print(f"[ERROR] Model file too small: {file_size} bytes")
        return False

    # Try to load with OpenCV
    try:
        detector = cv2.FaceDetectorYN.create(model_path, "", (320, 320))
        print(f"[OK] Model verified successfully: {model_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Model validation failed: {str(e)}")
        return False


def check_opencv_version() -> tuple:
    """
    Check OpenCV version and YuNet compatibility
    
    Returns:
        Tuple of (major, minor, patch) version numbers
    """
    version_str = cv2.__version__
    version_parts = version_str.split('.')
    
    try:
        major = int(version_parts[0])
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        patch = int(version_parts[2]) if len(version_parts) > 2 else 0
        return (major, minor, patch)
    except (ValueError, IndexError):
        return (0, 0, 0)


def check_yunet_compatibility() -> bool:
    """
    Check if current OpenCV version supports YuNet (requires >= 4.8)
    
    Returns:
        True if compatible, False otherwise
    """
    major, minor, patch = check_opencv_version()
    version_str = cv2.__version__
    
    if major < 4 or (major == 4 and minor < 8):
        print(f"[ERROR] YuNet requires OpenCV >= 4.8.0, found {version_str}")
        print(f"   Upgrade with: pip install --upgrade opencv-python>=4.8")
        return False

    # Check if FaceDetectorYN exists
    if not hasattr(cv2, 'FaceDetectorYN'):
        print(f"[ERROR] cv2.FaceDetectorYN not found in OpenCV {version_str}")
        print(f"   You may need opencv-contrib-python for YuNet support")
        return False

    print(f"[OK] OpenCV {version_str} supports YuNet")
    return True


if __name__ == "__main__":
    print("YuNet Model Download Utility")
    print("=" * 50)
    
    # Check compatibility
    print("\n1. Checking OpenCV compatibility...")
    if not check_yunet_compatibility():
        exit(1)
    
    # Download model
    print("\n2. Downloading YuNet model...")
    success = download_yunet_model()
    
    if success:
        # Verify model
        print("\n3. Verifying model...")
        model_path = get_yunet_model_path(auto_download=False)
        if model_path and verify_yunet_model(model_path):
            print("\n[OK] YuNet model ready to use!")
            print(f"   Location: {model_path}")
        else:
            print("\n[ERROR] Model verification failed")
            exit(1)
    else:
        print("\n[ERROR] Model download failed")
        exit(1)
