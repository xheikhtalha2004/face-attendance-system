"""
Migration: Add soft delete support to students table
This migration adds a deleted_at column to enable soft deletes
instead of hard deletes, allowing deleted student IDs to be reused
"""
from sqlalchemy import text

def migrate():
    """Apply migration"""
    from db import db
    
    try:
        # Add deleted_at column if it doesn't exist
        db.session.execute(text('''
            ALTER TABLE students ADD COLUMN deleted_at DATETIME DEFAULT NULL
        '''))
        
        # Create index on deleted_at
        db.session.execute(text('''
            CREATE INDEX IF NOT EXISTS idx_students_deleted_at ON students(deleted_at)
        '''))
        
        db.session.commit()
        print("✓ Soft delete migration applied successfully")
        return True
    except Exception as e:
        db.session.rollback()
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("✓ Soft delete column already exists, skipping migration")
            return True
        print(f"✗ Migration error: {str(e)}")
        return False

if __name__ == '__main__':
    migrate()
