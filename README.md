# FaceAttend Pro - Face Recognition Attendance System

Complete face recognition-based attendance management system with Flask backend and React frontend.

## 🚀 Quick Start

### Prerequisites
- Python 3.11.x (venv already created)
- Node.js (for frontend)

### Backend Setup

1. **Navigate to backend folder**:
   ```bash
   cd backend
   ```

2. **Activate virtual environment**:
   ```bash
   # On Windows
   ..\venv\Scripts\activate
   
   # On Linux/Mac
   source ../venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**:
   ```bash
   python app.py
   ```

   Server will start at `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend folder**:
   ```bash
   cd frontend
   ```

2. **Install dependencies** (if not done):
   ```bash
   npm install
   ```

3. **Run development server**:
   ```bash
   npm run dev
   ```

   Frontend will start at `http://localhost:5173`

## 📁 Project Structure

```
CV Project/
├── frontend/              # React + TypeScript frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── context/       # State management
│   │   ├── services/      # API integration
│   │   └── utils/         # Helper functions
│   └── package.json
├── backend/               # Flask API server
│   ├── app.py            # Main Flask application
│   ├── db.py             # Database models
│   ├── requirements.txt
│   └── .env              # Configuration
├── ml_cvs/               # Machine Learning & Computer Vision
│   ├── face_detection.py
│   ├── face_alignment.py
│   ├── embedding_extractor.py
│   └── recognition.py
└── README.md
```

## 🎯 Features

### Backend
- ✅ RESTful API with Flask
- ✅ JWT Authentication
- ✅ SQLite Database with SQLAlchemy ORM
- ✅ Face detection with OpenCV
- ✅ Face alignment for accuracy
- ✅ 128D embedding extraction (FaceNet-based)
- ✅ Real-time face recognition
- ✅ Duplicate detection prevention

### Frontend
- ✅ Modern React UI with TypeScript
- ✅ Real-time webcam feed
- ✅ Student registration with photo capture
- ✅ Live attendance tracking
- ✅ Dashboard with analytics
- ✅ Attendance reports (CSV export)
- ✅ System settings

## 🔧 Configuration

### Backend (.env)
- `FLASK_ENV`: development/production
- `DATABASE_URL`: Database connection string
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `CONFIDENCE_THRESHOLD`: Face recognition confidence (0.6)
- `LATE_THRESHOLD_MINUTES`: Minutes after class start considered late

### Frontend (.env.local)
- `VITE_API_URL`: Backend API URL (http://localhost:5000/api)

## 📝 Usage

### 1. First Time Setup
1. Start backend server
2. Register admin user via `/api/auth/register`
3. Login to get JWT token

### 2. Register Students
1. Navigate to "Student Registry"
2. Click "Add New Student"
3. Fill in details and capture photo
4. System will extract face encoding

### 3. Live Attendance
1. Navigate to "Live Attendance"
2. System will start webcam
3. As students appear, they will be recognized automatically
4. Attendance is marked with timestamp and confidence score

### 4. View Reports
1. Navigate to "Reports"
2. Select date range
3. Export as CSV if needed

## 🔐 API Endpoints

### Authentication
- `POST /api/auth/register` - Register admin
- `POST /api/auth/login` - Login

### Students
- `GET /api/students` - List all students
- `POST /api/students` - Register student (with photo)
- `PUT /api/students/{id}` - Update student
- `DELETE /api/students/{id}` - Delete student

### Attendance
- `GET /api/attendance` - Get attendance records
- `POST /api/recognize` - Recognize face from frame
- `POST /api/attendance/mark` - Manual attendance

### Settings
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings

## 🧪 Testing

### Backend
```bash
cd backend
python -m pytest tests/
```

### Frontend
```bash
cd frontend
npm run test
```

## 🤝 Contributing

Follow SRDS Development Guide:
- Use feature branches
- Create pull requests for review
- Write unit tests
- Follow code review process

## 📄 License

MIT License

## 👥 Team

Developed following SRDS (Software Requirements & Development Specifications)

---

**Note**: This system uses face recognition technology. Ensure compliance with privacy regulations in your jurisdiction.
