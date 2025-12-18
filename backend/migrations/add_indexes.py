"""
Utility migration to add performance indexes and the sessions.notes column.
Designed to be idempotent and safe to re-run.
"""
import os
from sqlalchemy import create_engine, text


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data.db")


def ensure_notes_column(conn):
    """Add notes column to sessions table if missing (SQLite compatible)."""
    # Only implemented for SQLite; extend as needed for other engines
    pragma = conn.execute(text("PRAGMA table_info('sessions')")).mappings().all()
    column_names = {row["name"] for row in pragma}
    if "notes" not in column_names:
        conn.execute(text("ALTER TABLE sessions ADD COLUMN notes TEXT"))
        print("Added sessions.notes column")
    else:
        print("sessions.notes column already present")


def create_indexes(conn):
    """Create common indexes for faster lookups."""
    statements = [
        "CREATE INDEX IF NOT EXISTS idx_session_status ON sessions(status)",
        "CREATE INDEX IF NOT EXISTS idx_session_starts_at ON sessions(starts_at)",
        "CREATE INDEX IF NOT EXISTS idx_attendance_session_student ON attendance(session_id, student_id_fk)",
        "CREATE INDEX IF NOT EXISTS idx_attendance_checkin ON attendance(check_in_time)",
        "CREATE INDEX IF NOT EXISTS idx_enrollment_course ON enrollments(course_id)",
    ]
    for stmt in statements:
        conn.execute(text(stmt))
    print("Indexes ensured/created")


def main():
    engine = create_engine(DATABASE_URL)
    print(f"Using database: {DATABASE_URL}")
    with engine.begin() as conn:
        ensure_notes_column(conn)
        create_indexes(conn)
    print("Migration complete")


if __name__ == "__main__":
    main()
