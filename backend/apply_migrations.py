#!/usr/bin/env python3
"""
Apply pending database migrations
Run this script after pulling code changes that include database schema modifications
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

def apply_soft_delete_migration():
    """Apply the soft delete column migration"""
    try:
        from app import app
        from db import db
        from sqlalchemy import text
        
        with app.app_context():
            print("Applying soft delete migration...")
            
            # Check if column already exists
            inspector = db.inspect(db.engine)
            students_columns = [col['name'] for col in inspector.get_columns('students')]
            
            if 'deleted_at' in students_columns:
                print("✓ deleted_at column already exists, skipping migration")
                return True
            
            # Add deleted_at column
            try:
                db.session.execute(text('''
                    ALTER TABLE students ADD COLUMN deleted_at DATETIME DEFAULT NULL
                '''))
                db.session.commit()
                print("✓ Added deleted_at column to students table")
            except Exception as e:
                if "duplicate" in str(e).lower():
                    print("✓ Column already exists")
                else:
                    raise
            
            # Create index for deleted_at
            try:
                db.session.execute(text('''
                    CREATE INDEX idx_students_deleted_at ON students(deleted_at)
                '''))
                db.session.commit()
                print("✓ Created index on deleted_at column")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("✓ Index already exists")
                else:
                    raise
            
            print("\n✓ Soft delete migration completed successfully!")
            print("\nNow students can be re-registered with previously deleted IDs.")
            return True
            
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = apply_soft_delete_migration()
    sys.exit(0 if success else 1)
