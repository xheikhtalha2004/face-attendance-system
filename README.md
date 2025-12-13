# Face Attendance System - Enhanced Version

## 🎯 Overview

Production-ready face attendance system with InsightFace (RetinaFace + ArcFace), multi-frame confirmation, quality gates, automated timetable management, and session-based tracking.

### Key Features ✨

- **InsightFace Integration** - buffalo_l model (512D ArcFace embeddings)
- **Multi-frame Confirmation** - K-of-N voting (5 out of 10 frames) prevents false positives
- **Quality Gates** - Blur detection, face size check, angle estimation
- **Multi-embedding Enrollment** - 5-15 samples per student for robust recognition
- **Session-based Attendance** - No duplicates, automatic PRESENT/LATE determination
- **Automated Timetable** - Auto-creates sessions from weekly schedule
- **Scheduler Service** - Background task for session management and absentee marking

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend)
- Webcam for face capture
- ~2GB disk space (for InsightFace models)

### Installation

#### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and set:
# DATABASE_URL=sqlite:///data.db
# JWT_SECRET_KEY=your-secret-key-here
# UPLOAD_FOLDER=uploads

# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✓ Database initialized')"

# Run server
python app.py
```

Server runs at: `http://localhost:5000`

#### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:5000" > .env

# Start dev server
npm run dev
```

Frontend runs at: `http://localhost:5173`

---

## 📚 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Flask Backend (Port 5000)                 │
├──────────────────────┬──────────────────┬───────────────────┤
│   Authentication     │  Student Mgmt    │  Timetable API    │
│   (JWT)              │  + Enrollment    │  (Blueprint)      │
└──────────────────────┴──────────────────┴───────────────────┘
           │                      │                   │
    ┌──────▼──────┐      ┌───────▼──────┐    ┌──────▼──────┐
    │  SQLAlchemy │      │   Enrollment │    │   Scheduler │
    │  Database   │      │   Service    │    │   Service   │
    └─────────────┘      └───────┬──────┘    └──────┬──────┘
                                 │                   │
          ┌──────────────────────┴───────────────────┘
          │
    ┌─────▼──────────────────────────────────────────┐
    │           ML/CV Pipeline (ml_cvs/)             │
    ├────────────┬──────────────┬────────────────────┤
    │FaceEngine  │  Quality     │  Stabilizer        │
    │(InsightFace│  Gates       │  (K-of-N)          │
    └────────────┴──────────────┴────────────────────┘
```

### Database Schema

**Tables:**
- `users` - Admin authentication
- `students` - Student records with legacy face_encoding
- `student_embeddings` - Multiple embeddings per student (NEW)
- `courses` - Course master data (NEW)
- `time_slots` - Weekly timetable grid (NEW)
- `sessions` - Class sessions (auto or manual) (NEW)
- `attendance` - Session-based attendance records (UPDATED)

---

## 🔧 Configuration

**Key Settings:** [ml_cvs/config.py](ml_cvs/config.py)

```python
# Face Recognition
INSIGHTFACE_MODEL = 'buffalo_l'  # Best accuracy
SIMILARITY_THRESHOLD = 0.35      # Tune: 0.30-0.45

# Quality Gates
MIN_FACE_SIZE = 80
BLUR_THRESHOLD = 100.0
YAW_MAX = 25  # ±25° left-right
PITCH_MAX = 20  # ±20° up-down

# Stabilization (K-of-N)
K_MATCHES_REQUIRED = 5
N_FRAME_WINDOW = 10
COOLDOWN_SECONDS = 120

# Timetable
SLOT_TIMES = {
    1: {'start': '08:30', 'end': '09:50'},
    2: {'start': '09:50', 'end': '11:10'},
    3: {'start': '11:10', 'end': '12:30'},
    4: {'start': '13:30', 'end': '14:50'},
    5: {'start': '14:50', 'end': '16:10'}
}
```

---

## 📖 API Reference

### Authentication

```http
POST /api/auth/login
POST /api/auth/register
```

### Students & Enrollment

```http
GET    /api/students
POST   /api/students                     # Legacy single-image enrollment
POST   /api/students/:id/enroll-frames   # Multi-frame enrollment (10-20 frames)
PUT    /api/students/:id
DELETE /api/students/:id
```

### Courses

```http
GET    /api/courses
POST   /api/courses
PUT    /api/courses/:id
DELETE /api/courses/:id
```

### Timetable

```http
GET    /api/timetable                # Get weekly schedule
POST   /api/timetable/slots          # Assign course to slot
DELETE /api/timetable/slots/:id      # Remove slot
```

### Sessions

```http
POST   /api/sessions                       # Create manual session
GET    /api/sessions/:id
GET    /api/sessions/active                # Get current active session
GET    /api/sessions/:id/attendance
PUT    /api/sessions/:id/status
POST   /api/sessions/:id/mark-absentees
```

### Recognition

```http
POST   /api/recognize
Body: { "image": "data:image/jpeg;base64,..." }

Response (verifying):
{
  "recognized": true,
  "confirmed": false,
  "verifying": true,
  "studentName": "John Doe",
  "message": "Verifying... (3/5)",
  "progress": { "matched": 3, "required": 5 }
}

Response (confirmed):
{
  "recognized": true,
  "confirmed": true,
  "studentName": "John Doe",
  "confidence": 0.876,
  "message": "Attendance marked: PRESENT",
  "session": {...},
  "attendance": {...}
}
```

---

## 🎓 Enrollment Guide

### Multi-frame Enrollment (Recommended)

**Frontend:**
```javascript
// Capture 15 frames over 3 seconds
const frames = [];
for (let i = 0; i < 15; i++) {
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  frames.push(canvas.toDataURL('image/jpeg', 0.9));
  await sleep(200); // 200ms interval
}

// Send to backend
const response = await fetch(`/api/students/${studentId}/enroll-frames`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    frames: frames,
    maxEmbeddings: 10
  })
});
```

**Backend Processing:**
1. Decodes base64 images
2. Detects faces in each frame
3. Applies quality gates (blur, size, angle)
4. Scores frames by: detection confidence (50%) + sharpness (30%) + angle (20%)
5. Keeps top 10 embeddings
6. Stores to `student_embeddings` table

---

## 📅 Timetable & Auto-Sessions

### Setup Weekly Schedule

1. **Create Courses:**
   ```http
   POST /api/courses
   { "courseId": "CS101", "courseName": "Computer Science", "professorName": "Dr. Smith" }
   ```

2. **Assign to Time Slots:**
   ```http
   POST /api/timetable/slots
   {
     "dayOfWeek": "MONDAY",
     "slotNumber": 1,
     "courseId": 1,
     "startTime": "08:30",
     "endTime": "09:50",
     "lateThresholdMinutes": 5
   }
   ```

### Auto-Session Behavior

**Scheduler checks every minute:**
- At 08:30 → Auto-creates session for Slot 1
- Session status: `ACTIVE`
- Students recognized within 0-5 min → `PRESENT`
- Students recognized after 5 min → `LATE`
- At 08:35 (5 min after start) → Marks absent students as `ABSENT`
- Session status → `COMPLETED`

---

## 🧪 Testing

### Manual Testing Checklist

- [ ] Database initialization works
- [ ] InsightFace model downloads on first run (~500MB)
- [ ] Single student enrollment (legacy endpoint)
- [ ] Multi-frame enrollment (15 frames)
- [ ] Create course and time slot
- [ ] Auto-session creation (wait for slot time)
- [ ] Face recognition with quality gates
- [ ] K-of-N stabilization (verify 5/10 frames)
- [ ] Attendance marked as PRESENT
- [ ] Late arrival marked as LATE
- [ ] Absentee auto-marking

### Unit Tests (Recommended)

```bash
# Quality gates
python -m pytest tests/test_quality.py

# Stabilizer
python -m pytest tests/test_stabilizer.py

# Enrollment
python -m pytest tests/test_enrollment.py
```

---

## 🔍 Troubleshooting

### InsightFace Model Not Found

**Error:** `Model buffalo_l not found`

**Solution:**
- Models auto-download to `~/.insightface/`
- Requires internet connection on first run
- Manual download: https://github.com/deepinsight/insightface/tree/master/model_zoo

### Recognition Not Working

**Check:**
1. Is there an active session? (`GET /api/sessions/active`)
2. Are students enrolled with embeddings? (`GET /api/students`)
3. Check quality gates logs (blur, size, angle)
4. Verify K-of-N progress (`progress` field in response)

### Database Errors

**Reset database:**
```bash
rm data.db
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

---

## 📈 Performance

**Expected Metrics:**
- Face detection: 30-50ms per frame (CPU)
- Embedding extraction: 40-60ms per face
- Quality gates: 5-10ms
- Full recognition cycle: ~100ms per frame
- K-of-N confirmation: 1-2 seconds (10 frames @ 5 FPS)

**Memory Usage:**
- Buffalo_l model: ~500MB RAM
- Per session: ~10MB
- Per student (10 embeddings): ~20KB

**Optimization Tips:**
- Use GPU: Set `USE_GPU = True` in config (requires CUDA + onnxruntime-gpu)
- Reduce frame rate: Process every 2nd-3rd frame
- Lower K-of-N: Use K=3, N=7 for faster confirmation

---

## 📝 License

MIT License - See LICENSE file

---

## 🙏 Credits

- **InsightFace** - https://github.com/deepinsight/insightface
- **Flask** - https://flask.palletsprojects.com/
- **React** - https://react.dev/
- **APScheduler** - https://apscheduler.readthedocs.io/

---

## 📞 Support

For issues or questions:
- Check [Implementation Plan](docs/implementation_plan.md)
- Review [API Documentation](docs/api.md)
- Contact: [your-email@example.com]

---

**Status:** ✅ Backend Complete | ⏳ Frontend Pending  
**Version:** 2.0.0 (Enhanced with InsightFace)  
**Last Updated:** December 13, 2025
