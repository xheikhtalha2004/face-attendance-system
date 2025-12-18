# QUICK REFERENCE CARD

## 🎯 What Was Implemented

### Before
- ❌ Database deleted on each run
- ❌ No way to delete/update students
- ❌ No manual session creation
- ❌ Sessions status not tracked properly
- ❌ No data verification

### After
- ✅ Database PRESERVED between runs
- ✅ Edit/Delete students with UI buttons
- ✅ Manual session creation with timestamps
- ✅ Sessions properly tracked (SCHEDULED→ACTIVE→COMPLETED)
- ✅ Built-in data verification with "Verify Data & Timestamps" button

---

## 🔧 UI Navigation

### Navbar Buttons (Left to Right)
```
Dashboard → Recognition → Testing → Attendance → Register → Timetable → Reports → Students (NEW) → Sessions (NEW)
```

### Students Tab
```
✓ View all registered students
✓ Edit: Click "Edit" button, modify fields, click "Save"
✓ Delete: Click "Delete" button, confirm in dialog
✓ Shows: Name, Roll Number, Email, Phone, Department
```

### Sessions Tab
```
✓ Create manual session: Select course → Set times → Click "Create Session"
✓ Activate: Click "Activate" button (SCHEDULED → ACTIVE)
✓ End: Click "End" button (ACTIVE → COMPLETED)
✓ Cancel: Click "Cancel" button (cancel any session)
✓ Filter: Use dropdown to filter by status
✓ Verify: Click "Verify Data & Timestamps" button
```

---

## 🗄️ Database State

| Entity | Before | After |
|--------|--------|-------|
| Database | Deleted on restart | **PRESERVED** |
| Students | No edit/delete | **Edit & Delete options** |
| Sessions | Auto-created only | **Manual creation too** |
| Status | No tracking | **SCHEDULED→ACTIVE→COMPLETED** |
| Timestamps | Not verified | **Verification built-in** |

---

## 🚀 Workflow: Create & Run Session Manually

1. **Create Course** (if needed)
   - Go to Timetable tab
   - Add course: CS-101, Introduction to CS, Prof. Smith
   - Click "Add"

2. **Create Session**
   - Go to Sessions tab
   - Select course from dropdown
   - Set Start Time: e.g., 10:00 AM
   - Set End Time: e.g., 11:00 AM
   - Click "Create Session"
   - Status: SCHEDULED

3. **Activate Session**
   - When class is ready to start
   - Click "Activate" button
   - Status: ACTIVE

4. **Mark Attendance** (during class)
   - Go to Recognition tab
   - Show face to camera
   - Attendance automatically marked

5. **End Session**
   - When class is over
   - Click "End" button
   - Status: COMPLETED
   - End time automatically updated

6. **Verify Everything**
   - Click "Verify Data & Timestamps"
   - See complete report:
     - ✓ Session count by status
     - ✓ Attendance records count
     - ✓ All timestamps saved
     - ✓ Message: "All timestamps are stored properly"

---

## 🧪 API Testing

### Test Student Operations
```bash
# List all students
curl http://localhost:5000/api/students

# Get student details
curl http://localhost:5000/api/students/1

# Get student embeddings
curl http://localhost:5000/api/students/1/embeddings

# Get student attendance
curl http://localhost:5000/api/students/1/attendance-records
```

### Test Session Operations
```bash
# List all sessions
curl http://localhost:5000/api/sessions

# List active sessions only
curl http://localhost:5000/api/sessions/active

# Filter by date
curl http://localhost:5000/api/sessions?date=2025-12-17

# Verify data integrity
curl http://localhost:5000/api/sessions/verify-data
```

### Test with Python Script
```bash
python backend/test_management_api.py
```

---

## 💾 Data Persistence

### What's Saved
✅ Student records (name, roll number, email, phone, dept)
✅ Face embeddings (automatically during registration)
✅ Attendance records (timestamp, status, method)
✅ Sessions (course, times, status)
✅ Timetable (courses, time slots)

### What's NOT Saved
- Temporary cache files
- Session cookies
- API logs (unless enabled)

### How to Delete
1. **Delete a Student:**
   - Go to Students tab
   - Click "Delete" on any student
   - Confirm in dialog
   - All related records deleted automatically

2. **Delete a Session:**
   - Go to Sessions tab
   - Click "Cancel" (marks as CANCELLED)
   - Data still kept (not removed)

3. **Hard Delete Database:**
   - Close backend
   - Delete `backend/instance/data.db` OR `instance/data.db`
   - Restart backend (recreates fresh DB)

---

## ⏰ Timestamp Format

All timestamps stored in **ISO 8601**:
```
2025-12-17T14:30:00           (local time)
2025-12-17T14:30:00+05:00     (with timezone)
```

When querying by date:
```
?date=2025-12-17              (YYYY-MM-DD format)
```

---

## 🐛 Troubleshooting

### "Failed to load students" or "Failed to load sessions"
- ✓ Check backend is running on port 5000
- ✓ Check for errors in backend terminal
- ✓ Refresh page (Ctrl+R)

### "Cannot delete student"
- ✓ Confirm dialog appeared?
- ✓ Check backend has no errors
- ✓ Try again

### "Session status not updating"
- ✓ Click Refresh button
- ✓ Check backend logs for errors
- ✓ Verify backend is still running

### "Data verification shows 0 records"
- ✓ Create a student or session first
- ✓ Then click Verify again
- ✓ Normal if system is empty

---

## 📱 Mobile / Responsive

✅ All new components responsive
✅ Tables collapse on mobile
✅ Buttons stack on small screens
✅ Full functionality on all sizes

---

## 🔐 Security Notes

⚠️ Development build:
- No authentication
- No rate limiting
- All endpoints accessible
- For production: Add authentication, HTTPS, rate limits

---

## 📞 Need Help?

1. **Check Logs:**
   - Backend terminal shows detailed errors
   - Browser console (F12 → Console tab)

2. **Read Documentation:**
   - `DATABASE_MANAGEMENT_GUIDE.md` - Full feature guide
   - `IMPLEMENTATION_COMPLETE.md` - What was done
   - This file - Quick reference

3. **Test API:**
   - Run `python backend/test_management_api.py`
   - Shows all working/failing endpoints

---

**Last Updated:** 2025-12-17
**Status:** ✅ Complete & Ready to Use
