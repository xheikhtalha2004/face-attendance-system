"""
Download InsightFace Models
Downloads the buffalo_l model files required for face detection and recognition
"""
import insightface
from insightface.app import FaceAnalysis

print("Downloading InsightFace buffalo_l model...")
print("This may take a few minutes (~150MB download)")

try:
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    print("✓ Model downloaded and initialized successfully!")
    print(f"✓ Models detected: {list(app.models.keys())}")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
