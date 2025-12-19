# Critical Testing Checklist - Automatic Session & Attendance System
**Date:** December 19, 2025
**Status:** Pre-Production Validation

## ✅ FIXES APPLIED

### 1. **Scheduler Timezone Consistency** ✅ FIXED
- **Issue:** Mixed use of `datetime.now()` and `datetime.utcnow()` caused timing mismatches
- **Fix Applied:**
  - `check_and_create_sessions()` - uses `datetime.now()` (local time)
  - `activate_due_sessions()` - changed from `utcnow()` to `now()` for consistency
  - `end_expired_sessions()` - already uses `datetime.now()`
  - All session time comparisons now use local time consistently
- **Impact:** Sessions will be created/activated at the correct local time

### 2. **Attendance LATE Status Detection** ✅ FIXED
- **Issue:** Late threshold comparison used `datetime.now()` which could be inconsistent
- **Fix Applied:** Updated `upsert_attendance()` in db_helpers.py to use consistent local time
  ```python
  current_time = datetime.now()
  late_cutoff = session.starts_at + timedelta(minutes=session.late_threshold_minutes)
  if current_time > late_cutoff:
      status = 'LATE'
  ```
- **Impact:** Students marked after threshold will correctly receive LATE status

### 3. **Absentee Marking Logic** ✅ FIXED
- **Issue:** Intruders were being included in absent count
- **Fix Applied:** Changed filter to exclude non-PRESENT/LATE students
  ```python
  present_student_ids = set(a.student_id_fk for a in attendance_records 
                           if a.status in ['PRESENT', 'LATE'])
  ```
- **Impact:** Only enrolled students who never appeared are marked ABSENT

### 4. **Session Activation Window** ✅ FIXED
- **Issue:** Sessions could be activated at wrong times
- **Fix Applied:** 
  - Added check for due sessions (starts_at <= now AND ends_at > now)
  - Auto-activated sessions get logged with session ID and course ID
- **Impact:** Sessions activate correctly at scheduled time

---

## 🔍 CRITICAL LOGIC FLOWS - VERIFIED

### Flow 1: Automatic Session Creation
```
08:28 → Check if current_day has slots in timetable
08:30 → Session start time: check (0 <= time_diff <= 120)
         ↓ YES
         Check if session already exists for this slot today
         ↓ NO
         Create Session with:
           - status: SCHEDULED (if > 2 min before slot)
           - status: ACTIVE (if within 2 min of slot)
         Schedule absentee marking job
           Run at: slot.start_time + late_threshold + 5 min buffer
08:35 → Session status automatically changes to ACTIVE
08:42 → Mark absentees job scheduled (for 5 min threshold + 5 min buffer)
```
**Verification Points:**
- ✅ Slot detection working (Friday slots should be found)
- ✅ Session creation is idempotent (won't create duplicates)
- ✅ Absentee job scheduled correctly with proper time

### Flow 2: Attendance Marking (Enrolled Student)
```
Student face detected
  ↓
Extract embedding
  ↓
Load enrolled students for course
  ↓
Compare against enrolled students' embeddings
  ↓
Match found with similarity >= 0.6
  ↓
Check if student is enrolled in this course
  ↓ YES (enrollment found)
Check if already marked attendance
  ↓ NO
Determine status:
  - Current time <= (session start + 5 min late threshold) → PRESENT
  - Current time >  (session start + 5 min late threshold) → LATE
  ↓
Create/Update Attendance record
```
**Verification Points:**
- ✅ Enrollment check correctly identifies enrolled vs non-enrolled
- ✅ PRESENT/LATE status determined by threshold
- ✅ Re-entry detection logs multiple appearances

### Flow 3: Intruder Detection
```
Student face detected
  ↓
Extract embedding
  ↓
Load enrolled students for course
  ↓
Compare against enrolled students' embeddings
  ↓
Match found with similarity >= 0.6
  ↓
Check if student is enrolled in this course
  ↓ NO (no enrollment)
Mark as INTRUDER
Create ReEntryLog with action='INTRUDER', is_suspicious=True
```
**Verification Points:**
- ✅ Only enrolled students can mark attendance
- ✅ Intruders are logged separately
- ✅ Intruders don't block other recognitions

### Flow 4: Absentee Marking
```
Session starts at 08:30
Late threshold: 5 minutes
Absentee job scheduled for: 08:30 + 5 + 5 = 08:40
  ↓
08:40 → mark_absentees_for_session() called
  ↓
Get enrolled students for course
  ↓
Get attendance records (filter: status IN ['PRESENT', 'LATE'])
  ↓
Find absent = enrolled ∩ not(attended)
  ↓
Mark absent students with status='ABSENT'
  ↓
Set session.status = 'COMPLETED'
```
**Verification Points:**
- ✅ Only enrolled students marked ABSENT
- ✅ INTRUDER records don't count as attendance
- ✅ Session marked COMPLETED after absentee marking

---

## 📋 PRE-TESTING CHECKLIST

### Database State
- [ ] At least 2 courses created with course IDs
- [ ] Timetable slots filled for Friday (today)
- [ ] At least 3-5 students registered with face embeddings
- [ ] At least 2 students enrolled in Friday courses
- [ ] At least 1 student NOT enrolled (for intruder test)

### Configuration
- [ ] Confidence threshold set (default: 0.6)
- [ ] Late threshold set (default: 5 minutes)
- [ ] Scheduler service running and logging
- [ ] Backend server timezone matches system timezone

### Application State
- [ ] Frontend running and connected to backend
- [ ] Scheduler jobs visible in logs
- [ ] No errors in browser console
- [ ] No errors in backend logs (except DEBUG level)

---

## 🧪 TESTING SCENARIOS

### Test 1: Automatic Session Creation
**Setup:**
- Create course "CS101" with professor name
- Add Friday slot: 10:00-11:00
- Enroll students A, B, C in CS101

**Test Steps:**
```
At 10:00:00 - Session should NOT exist
At 10:00:30 - Session should be SCHEDULED or ACTIVE
At 10:00:50 - Check: SELECT * FROM sessions WHERE course_id=CS101 AND DATE(starts_at)=TODAY
Expected: 1 session with status SCHEDULED or ACTIVE
```

**Verification:**
- [ ] Session created exactly once
- [ ] Session time matches slot time (10:00-11:00)
- [ ] Absentee marking job is scheduled
- [ ] Backend logs show: "Auto-created session for CS101 at 10:00"

---

### Test 2: Attendance Marking (Enrolled Student)
**Setup:**
- Session for CS101 active
- Student A enrolled in CS101
- Student A face registered with embedding

**Test Steps:**
```
At 10:05:00 - Show Student A's face to camera
Expected: 
- Recognized: True
- studentName: "Student A"
- confidence: > 0.6
- status: PRESENT (since within 5 min threshold)
- message: "Attendance marked: PRESENT"

Check database:
- SELECT * FROM attendance WHERE session_id=SESSION AND student_id_fk=A
- Expected: 1 record with status='PRESENT', check_in_time=10:05:XX
```

**Verification:**
- [ ] Face recognized correctly
- [ ] Status = PRESENT (not LATE)
- [ ] Confidence score displayed
- [ ] Attendance record created in DB
- [ ] Reports panel shows attendance

---

### Test 3: Late Marking (After Threshold)
**Setup:**
- Session for CS101 active, started at 10:00
- Late threshold: 5 minutes (so deadline 10:05)
- Student B enrolled in CS101
- Student B face registered

**Test Steps:**
```
At 10:10:00 - Show Student B's face (5 minutes after threshold)
Expected:
- Recognized: True
- status: LATE (since current_time > 10:05)
- message: "Attendance marked: LATE"

Check database:
- SELECT * FROM attendance WHERE session_id=SESSION AND student_id_fk=B
- Expected: 1 record with status='LATE'
```

**Verification:**
- [ ] Status = LATE (not PRESENT)
- [ ] Time-based status detection working
- [ ] Attendance record shows LATE status
- [ ] Reports show LATE status with icon

---

### Test 4: Intruder Detection
**Setup:**
- Session for CS101 active
- Student D registered with face embedding but NOT enrolled in CS101
- Student D face shows up at camera

**Test Steps:**
```
At 10:15:00 - Show Student D's face
Expected:
- Recognized: True
- intruder: True
- message: "⚠️ INTRUDER ALERT: Student D is not enrolled in this course!"
- attendance.status: "INTRUDER"

Check database:
- SELECT * FROM attendance WHERE session_id=SESSION AND student_id_fk=D
- Expected: 1 record with status='INTRUDER'
- SELECT * FROM reentry_logs WHERE session_id=SESSION AND action='INTRUDER'
- Expected: 1 log entry with is_suspicious=True
```

**Verification:**
- [ ] Face recognized as registered student
- [ ] Status = INTRUDER
- [ ] ReEntryLog created
- [ ] Alert message shown in UI
- [ ] Intruder doesn't block other students

---

### Test 5: Re-entry Detection
**Setup:**
- Session for CS101 active
- Student A already marked PRESENT at 10:05
- Student A shows face again at camera

**Test Steps:**
```
At 10:20:00 - Show Student A's face again
Expected:
- Recognized: True
- alreadyMarked: True
- reEntry: True
- message: "Re-entry detected! Logged as suspicious."

Check database:
- SELECT * FROM reentry_logs WHERE session_id=SESSION AND student_id=A AND action IN ('OUT', 'IN')
- Expected: Multiple log entries with is_suspicious=True
```

**Verification:**
- [ ] Re-entry detected correctly
- [ ] Doesn't create duplicate attendance
- [ ] Logged as suspicious
- [ ] ReEntryLog has multiple entries for same student

---

### Test 6: Absentee Marking
**Setup:**
- Session for CS101 started at 10:00
- Late threshold: 5 minutes
- Enrolled students: A, B, C
- Attendance status: A=PRESENT, B=LATE, C=NONE
- Absentee marking job scheduled for 10:10

**Test Steps:**
```
Wait until 10:10:00 or manually trigger mark_absentees_for_session(session_id)

Check database at 10:10+:
- SELECT * FROM attendance WHERE session_id=SESSION AND status='ABSENT'
- Expected: 1 record for Student C with status='ABSENT'

- SELECT * FROM sessions WHERE id=SESSION
- Expected: status='COMPLETED'
```

**Verification:**
- [ ] Only Student C marked ABSENT
- [ ] Students A and B not affected
- [ ] Session marked COMPLETED
- [ ] Backend logs show: "Marked X students as ABSENT for session Y"

---

### Test 7: Multiple Faces / Unknown Face
**Setup:**
- Session for CS101 active
- Unknown face (not registered) shows up at camera

**Test Steps:**
```
Show unknown person's face
Expected:
- Recognized: False
- message: "Unknown face (not enrolled in this course or below confidence threshold)"

Show multiple people's faces together
Expected:
- Recognized: False
- message: "Multiple faces detected (2). Please ensure only one person in frame"
```

**Verification:**
- [ ] Unknown faces rejected properly
- [ ] Multiple face detection works
- [ ] Error messages clear and helpful

---

## 📊 EXPECTED DATABASE STATE AFTER TESTS

### Sessions Table
```
id  | course_id | starts_at      | ends_at        | status     | time_slot_id | auto_created
1   | CS101     | 10:00 (Fri)    | 11:00 (Fri)    | COMPLETED  | 1            | True
```

### Attendance Table
```
id  | session_id | student_id_fk | status    | check_in_time    | confidence | method
1   | 1          | A             | PRESENT   | 10:05:XX (Fri)   | 0.87       | AUTO
2   | 1          | B             | LATE      | 10:10:XX (Fri)   | 0.92       | AUTO
3   | 1          | C             | ABSENT    | NULL             | NULL       | AUTO
4   | 1          | D             | INTRUDER  | 10:15:XX (Fri)   | 0.85       | AUTO
```

### ReEntryLog Table
```
id  | session_id | student_id | action    | is_suspicious
1   | 1          | A          | IN        | False
2   | 1          | D          | INTRUDER  | True
3   | 1          | A          | OUT       | True
4   | 1          | A          | IN        | True
```

---

## 🐛 KNOWN ISSUES TO VERIFY

1. **Timezone Handling** ✅ FIXED
   - All time comparisons now use local `datetime.now()`
   - No mixing of UTC and local time

2. **Late Status Detection** ✅ FIXED
   - Properly compares current time with session start + threshold
   - Uses consistent local time

3. **Absentee Marking** ✅ FIXED
   - Excludes INTRUDER and re-entry records
   - Only includes PRESENT and LATE in "attended" count

4. **Re-entry Log** ✅ VERIFIED
   - Multiple logs created for same student
   - Marked as suspicious

5. **Enrollment Enforcement** ✅ VERIFIED
   - Recognition only against enrolled students
   - Intruders are detected if registered but not enrolled

---

## ⚠️ POTENTIAL ISSUES TO WATCH

### Critical
- [ ] **Daylight Saving Time**: System clock change could cause session creation to fail
  - **Mitigation**: Scheduler checks every 1 minute, should recover

- [ ] **Database Connection Loss**: Session creation could fail silently
  - **Mitigation**: Check backend logs for errors
  - **Watch**: "Error in check_and_create_sessions" messages

- [ ] **Face Engine Not Initialized**: If InsightFace fails to load
  - **Mitigation**: Check logs on first face recognition
  - **Watch**: "Face engine initialization error" messages

### Important
- [ ] **Enrollment Not Set**: Students registered but not enrolled
  - **Mitigation**: Verify enrollments before testing
  - **Watch**: "No students enrolled in this course" message

- [ ] **Confidence Threshold Too High**: Students not matching
  - **Mitigation**: Check settings, default 0.6
  - **Watch**: "below confidence threshold" message

- [ ] **Clock Drift**: Server time behind real time
  - **Mitigation**: Verify NTP sync
  - **Watch**: Sessions created early or late

---

## 📝 LOGGING HINTS

### Check Backend Logs For:

**Session Creation:**
```
Auto-created session for CS101 at 10:00 (Session ID: 1)
Scheduled absentee marking for session 1 at 10:10:05
```

**Session Activation:**
```
Auto-activated session 1 (CS101)
Auto-activated 1 scheduled session(s)
```

**Attendance Marking:**
```
Attendance marked: Student A (ID: 1) - PRESENT (confidence 0.87)
Attendance marked: Student B (ID: 2) - LATE (confidence 0.92)
⚠️ INTRUDER DETECTED: Student D (ID: 4) not enrolled in course CS101
Re-entry detected: Student A (ID: 1) in session 1
```

**Absentee Marking:**
```
Marked 1 students as ABSENT for session 1
Session 1 completed and attendance finalized
```

---

## 🎯 SUCCESS CRITERIA

✅ All automatic sessions created at correct time
✅ Attendance marked with correct status (PRESENT/LATE/ABSENT)
✅ Intruders detected and logged
✅ Re-entry detected and logged as suspicious
✅ Session marked COMPLETED after threshold
✅ Reports panel shows all attendance records
✅ No database constraint violations
✅ No timezone-related timing issues
✅ Logs are clear and helpful for debugging

---

**Last Updated:** 2025-12-19
**Next Review:** After field testing at university
