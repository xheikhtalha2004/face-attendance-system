"""
Database Migration Runner
Runs SQL migration scripts and updates schema
"""
import sqlite3
import os
from pathlib import Path

def run_migration(db_path, migration_file):
    """Run a SQL migration file"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(migration_file, 'r') as f:
        sql_script = f.read()
    
    try:
        cursor.executescript(sql_script)
        conn.commit()
        print(f"[OK] Migration applied: {migration_file}")
        return True
    except Exception as e:
        print(f"[ERROR] Migration failed: {migration_file}")
        print(f"Error: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    # Paths
    backend_dir = Path(__file__).parent
    db_path = backend_dir / 'instance' / 'data.db'
    migrations_dir = backend_dir / 'migrations'
    
    print(f"Database: {db_path}")
    print(f"Migrations: {migrations_dir}")
    
    # Ensure instance directory exists
    db_path.parent.mkdir(exist_ok=True)
    
    # Run all migration files
    if migrations_dir.exists():
        migration_files = sorted(migrations_dir.glob('*.sql'))
        for migration_file in migration_files:
            run_migration(db_path, migration_file)
    else:
        print("No migrations directory found")

if __name__ == '__main__':
    main()
