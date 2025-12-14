-- Migration: Add Enrollments and Re-entry Logs
-- Date: 2025-12-14
-- Description: Student course enrollment tracking and re-entry detection

-- Enrollments table (Student ↔ Course mapping)
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE(student_id, course_id)
);

-- Re-entry logs (track IN/OUT patterns for suspicious behavior)
CREATE TABLE IF NOT EXISTS re_entry_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    action VARCHAR(10) NOT NULL CHECK(action IN ('IN', 'OUT')),
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_suspicious BOOLEAN DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_reentry_session ON re_entry_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_reentry_student ON re_entry_logs(student_id);
CREATE INDEX IF NOT EXISTS idx_reentry_detected ON re_entry_logs(detected_at);
