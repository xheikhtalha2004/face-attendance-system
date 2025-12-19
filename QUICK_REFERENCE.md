# 🔍 QUICK REFERENCE CARD - DEBUGGING & VERIFICATION
**Print or Bookmark This!**

---

## 🚨 EMERGENCY CHECKS (If Something's Wrong)

### Session Not Creating at All
```bash
# 1. Check if scheduler is running
# Backend logs should show: "Session Scheduler Service initialized"

# 2. Verify timetable has Friday slot
SELECT * FROM time_slots WHERE day_of_week='FRIDAY';

# 3. Check system time
date

# 4. Manually trigger check (for testing)
# Send GET to: /api/sessions?date=TODAY
# Should return sessions created today
```

### Attendance Not Marking
```bash
# 1. Check if session is ACTIVE
SELECT * FROM sessions WHERE status='ACTIVE';

# 2. Check if student is enrolled
SELECT * FROM enrollments WHERE student_id=X AND course_id=Y;

# 3. Check face recognition logs
# Backend logs: "Attendance marked: Student X - PRESENT"

# 4. Check database
SELECT * FROM attendance WHERE session_id=X AND student_id_fk=Y;
```

### Wrong Status (LATE vs PRESENT)
```bash
# 1. Check session times
SELECT starts_at, late_threshold_minutes FROM sessions WHERE id=X;

# 2. Check attendance check_in_time
SELECT check_in_time FROM attendance WHERE session_id=X;

# 3. Calculate: 
# check_in_time > (starts_at + late_threshold_minutes)?
# If YES → should be LATE
# If NO → should be PRESENT
```

---

## 📊 KEY DATABASE QUERIES

### Session Status Check
```sql
-- Show all sessions for today
SELECT id, course_id, starts_at, ends_at, status, auto_created 
FROM sessions 
WHERE DATE(starts_at) = CURDATE()
ORDER BY starts_at;
```

### Attendance Status Distribution
```sql
-- Show attendance status breakdown for session
SELECT status, COUNT(*) as count 
FROM attendance 
WHERE session_id = <SESSION_ID>
GROUP BY status;
```

### Find Intruders
```sql
-- Show intruders detected
SELECT a.id, s.id as student_id, s.name, a.check_in_time, a.confidence
FROM attendance a
JOIN students s ON a.student_id_fk = s.id
WHERE a.status = 'INTRUDER'
ORDER BY a.check_in_time DESC
LIMIT 10;
```

### Find Re-entries
```sql
-- Show re-entry logs
SELECT l.id, l.student_id, s.name, l.action, l.is_suspicious, l.timestamp
FROM reentry_logs l
JOIN students s ON l.student_id = s.id
ORDER BY l.timestamp DESC
LIMIT 10;
```

### Enrollment Check
```sql
-- Check who's enrolled in a course
SELECT e.id, s.id, s.name, s.email
FROM enrollments e
JOIN students s ON e.student_id = s.id
WHERE e.course_id = <COURSE_ID>;
```

### Attendance Without Enrollment
```sql
-- Find anomalies (should be empty except INTRUDER)
SELECT a.id, a.student_id_fk, s.name, a.status
FROM attendance a
JOIN students s ON a.student_id_fk = s.id
LEFT JOIN enrollments e ON a.student_id_fk = e.student_id 
  AND (SELECT course_id FROM sessions WHERE id = a.session_id) = e.course_id
WHERE e.id IS NULL AND a.status != 'INTRUDER';
```

---

## 📝 LOG PATTERNS (What to Look For)

### ✅ Successful Session Creation
```
Auto-created session for CS101 at 10:00 (Session ID: 1)
Scheduled absentee marking for session 1 at 10:10:05
```

### ✅ Successful Attendance
```
Attendance marked: Student A (ID: 1) - PRESENT (confidence 0.87)
```

### ✅ Successful Absentee Marking
```
Marked 1 students as ABSENT for session 1
Session 1 completed and attendance finalized
```

### ❌ Session Creation Failed
```
No active slots for FRIDAY
-- Check: Is slot created in timetable?
```

### ❌ Attendance Marking Failed
```
No active session
-- Check: Is session ACTIVE in database?

Unknown face (not enrolled in this course or below confidence threshold)
-- Check: Is student enrolled? Is confidence > 0.6?

⚠️ INTRUDER DETECTED: Student D not enrolled in course
-- This is EXPECTED if student is registered but not enrolled
```

### ❌ Late Detection Wrong
```
Status should be LATE but shows PRESENT
-- Check: Is current time > (session_start + threshold)?
-- Check: Did upsert_attendance() run correctly?
```

---

## ⏱️ EXPECTED TIMELINE (Per Slot)

**Example: Friday 10:00-11:00 slot, 5 min threshold, 5 min buffer**

```
09:59:00 - Nothing happens
10:00:00 - Session creation check starts
10:00:30 - Session CREATED with status=SCHEDULED or ACTIVE
10:00:31 - Absentee marking JOB SCHEDULED for 10:10:05
10:00:50 - Next scheduler cycle, session already exists
10:01:00 - (If within 5-min activation window) Session status → ACTIVE
10:05:00 - Late deadline passes (start + 5 min)
10:05:01 - Any new attendance will be LATE
10:10:00 - Absentee marking job about to trigger
10:10:05 - Absentee marking job TRIGGERS
          - Enrolled students without PRESENT/LATE → ABSENT
          - Session status → COMPLETED
10:10:06 - No more attendance can be marked (session not ACTIVE)
```

**Key Times to Check:**
- `10:00:30` - Session should exist
- `10:01:00` - Session should be ACTIVE
- `10:10:05` - Absentee marking job runs
- `10:10:06` - Session should be COMPLETED

---

## 🎯 STATUS DETERMINATION LOGIC

```
if session.status != 'ACTIVE':
  ✗ Cannot mark attendance

if face NOT detected:
  ✗ "No face detected"

if multiple faces:
  ✗ "Multiple faces detected"

if face recognized:
  if already marked in session:
    ⚠️ "Re-entry detected" (suspicious)
  else if enrolled in course:
    if current_time <= (start + threshold):
      ✅ PRESENT
    else:
      ✅ LATE
  else:
    ⚠️ INTRUDER (not enrolled)
else:
  ✗ "Unknown face"
```

---

## 🔧 QUICK FIXES

### Session Creation Not Working
```
1. Check time: date
2. Check slot: SELECT * FROM time_slots WHERE day_of_week='FRIDAY'
3. Check logs: grep "Auto-created" backend.log
4. Restart scheduler if needed: kill backend, python app.py
```

### Late Status Not Working
```
1. Update late_threshold in timetable slot
2. Restart backend (new threshold applied at next check)
3. Verify in database: SELECT late_threshold_minutes FROM time_slots WHERE id=X
```

### Intruder Detection Not Working
```
1. Verify student IS registered: SELECT * FROM students WHERE id=X
2. Verify student NOT enrolled: SELECT * FROM enrollments WHERE student_id=X AND course_id=Y
3. Verify confidence > 0.6: Check backend logs for "confidence"
4. Try with higher quality image
```

---

## 🧮 CONFIDENCE THRESHOLD CALCULATION

**Current threshold:** 0.6 (can be changed)

```
Face similarity score ranges: 0.0 to 1.0

0.50 → Too lenient (many false positives)
0.55 → Lenient (some false positives)
0.60 → Moderate (balanced) ← CURRENT
0.65 → Strict (few false positives)
0.70 → Very strict (high false negatives)

To adjust:
UPDATE settings SET value = '0.65' WHERE key = 'confidence_threshold';

Restart backend for changes to take effect
```

---

## 🚨 CRITICAL STATUS CHECKS

### Before Deploying
- [ ] Time: `date` matches wall clock (±1 min)
- [ ] DB: `SELECT COUNT(*) FROM sessions;` returns number
- [ ] Slots: `SELECT COUNT(*) FROM time_slots WHERE day_of_week='FRIDAY';` > 0
- [ ] Students: `SELECT COUNT(*) FROM students;` > 0
- [ ] Enrollments: `SELECT COUNT(*) FROM enrollments;` > 0

### During Testing
- [ ] Backend logs show no errors (except DEBUG level OK)
- [ ] Session created at start time ±2 minutes
- [ ] Attendance marked instantly (<1 second)
- [ ] Status correct (PRESENT before threshold, LATE after)
- [ ] Absentee marking runs at correct time

### After Class
- [ ] Reports show all attendance
- [ ] Intruders logged separately
- [ ] Re-entries logged as suspicious
- [ ] No duplicate attendance records
- [ ] Session marked COMPLETED

---

## 📱 FRONTEND CHECKS

### Timetable Page
- [ ] Friday slots visible
- [ ] Slots show correct time and course
- [ ] Can edit slots

### Enhanced Recognition
- [ ] Camera starts
- [ ] Face detection works (shows bounding box)
- [ ] Recognition shows student name
- [ ] Confidence score displayed
- [ ] Status shows (PRESENT/LATE/INTRUDER)

### Reports Page
- [ ] Daily report shows attendance
- [ ] Can select session
- [ ] Session report shows correct attendance
- [ ] Can export CSV
- [ ] Status badges correct colors

---

## 🎓 REMEMBER

**Most Common Issues:**
1. System time wrong → Session creation fails
2. Student not enrolled → Intruder alert (expected)
3. Confidence too low → Face not recognized
4. Database connection lost → Check backend logs
5. Scheduler not running → Check backend started correctly

**Always Check Logs First!** ← Most issues visible in logs

**Database Queries Are Your Friend!** ← Verify state directly

**Confidence Score Most Important!** ← If < 0.6, won't recognize

---

**Keep This Document Handy at the University!**
**All queries and checks provided above.**
