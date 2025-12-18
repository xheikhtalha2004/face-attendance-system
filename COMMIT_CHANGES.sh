#!/bin/bash
# Commit and push all changes to GitHub

echo "
═══════════════════════════════════════════════════════════════════
 PREPARING TO COMMIT DATABASE MANAGEMENT & SESSION FEATURES
═══════════════════════════════════════════════════════════════════
"

# Add all new files
echo "📁 Adding new backend API files..."
git add backend/student_management_api.py backend/session_management_api.py backend/test_management_api.py

echo "📁 Adding new frontend components..."
git add frontend/src/components/StudentManagement.tsx frontend/src/components/SessionManagement.tsx

echo "📁 Adding documentation files..."
git add DATABASE_MANAGEMENT_GUIDE.md IMPLEMENTATION_COMPLETE.md QUICK_REFERENCE.md

# Add modified files
echo "📝 Adding updated files..."
git add backend/app.py frontend/src/App.tsx frontend/src/components/Navbar.tsx

# Show what will be committed
echo ""
echo "📋 Files to commit:"
git status --short

# Commit
echo ""
echo "💾 Committing changes..."
git commit -m "feat: Add database persistence and complete session management

- Database now preserved between runs (no auto-delete)
- Add Student Management: view, edit, delete students with cascade
- Add Session Management: manual create/activate/end with timestamps
- Fix session status tracking (SCHEDULED→ACTIVE→COMPLETED)
- Add data verification endpoint for timestamp integrity
- Add comprehensive documentation (3 guides)
- Add API testing script
- Update UI navigation (2 new tabs: Students, Sessions)

New Endpoints:
- GET/PUT/DELETE /api/students/<id> - Student operations
- POST /api/sessions/manual/create - Create manual session
- PUT /api/sessions/<id>/activate - Activate session
- PUT /api/sessions/<id>/end - End session
- GET /api/sessions/verify-data - Verify data integrity

All data with timestamps (ISO 8601) properly stored and retrievable."

# Push to GitHub
echo ""
echo "🚀 Pushing to GitHub..."
git push origin main

echo ""
echo "═══════════════════════════════════════════════════════════════════
 ✅ COMMIT COMPLETE
═══════════════════════════════════════════════════════════════════
"
