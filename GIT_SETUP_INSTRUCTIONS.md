# Git Setup and Push Instructions

## Step 1: Rename Repository on GitHub (Do this first on GitHub website)

1. Go to your GitHub repository
2. Click **Settings** tab
3. Scroll down to **Repository name**
4. Change it to: `face-attendance-system`
5. Click **Rename**

## Step 2: Run these commands in your terminal

```bash
cd "C:\Work\CV Project"

# Add all files
git add .

# Commit with comprehensive message
git commit -m "feat: Complete SRDS-compliant face recognition attendance system (Option C)

Major Implementation:
- Restructured to SRDS spec: frontend/, backend/, ml_cvs/ folders
- Flask REST API with 13 endpoints (auth, students, attendance, settings)
- Complete ML/CV pipeline: detection → alignment → embedding → recognition
- SQLAlchemy models: User, Student, Attendance, Settings
- Face recognition with 128D FaceNet embeddings
- JWT authentication and secure face encoding storage
- Frontend API service with axios and interceptors
- Automated setup.bat and run.bat scripts
- Comprehensive documentation (README, QUICKSTART, walkthrough)

Tech: Flask 3.0 + SQLAlchemy + face_recognition + OpenCV + React + TypeScript
Lines: 3,350+ across 15+ files
Status: Ready for submission"

# Create and switch to version2 branch
git checkout -b version2

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/face-attendance-system.git

# Push to version2 branch
git push -u origin version2
```

## Step 3: If repository doesn't exist yet

If you haven't created the GitHub repository yet:

1. Go to https://github.com/new
2. Repository name: `face-attendance-system`
3. Description: "SRDS-compliant face recognition attendance management system with Flask backend and React frontend"
4. Make it **Public** or **Private** (your choice)
5. **Don't** initialize with README (we already have one)
6. Click **Create repository**
7. Then run the commands from Step 2

## Quick Commands (Copy-Paste Ready)

```bash
# Navigate to project
cd "C:\Work\CV Project"

# Stage all changes
git add .

# Commit
git commit -m "feat: Complete SRDS-compliant face recognition attendance system"

# Create version2 branch
git checkout -b version2

# Add remote (UPDATE YOUR_USERNAME!)
git remote add origin https://github.com/YOUR_USERNAME/face-attendance-system.git

# Push
git push -u origin version2
```

## Verify

After pushing, you should see:
- Repository name: `face-attendance-system` 
- Branch: `version2`
- All files: backend/, frontend/, ml_cvs/, README.md, setup.bat, run.bat

## Troubleshooting

**If remote already exists:**
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/face-attendance-system.git
```

**If you need to force push:**
```bash
git push -f origin version2
```
