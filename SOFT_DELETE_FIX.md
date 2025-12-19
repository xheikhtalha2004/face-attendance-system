# Student ID Registration Fix - Soft Deletes Implementation

## Problem
Users couldn't re-register students with the same ID of previously deleted students. This was because:
- The `student_id` column had a `UNIQUE` constraint
- When a student was deleted (hard delete), the record was completely removed from the database
- However, the unique constraint prevented new registrations with the same ID

## Solution
Implemented **soft deletes** instead of hard deletes. This approach:
- Marks deleted students with a `deleted_at` timestamp instead of removing them
- Preserves student history and attendance records
- Allows student IDs to be reused by filtering out soft-deleted records in queries
- Maintains data integrity for historical reports

## Changes Made

### 1. Database Schema (`backend/db.py`)
- Added `deleted_at` column to the Student model
- This column is `NULL` for active students and contains a timestamp for deleted students

### 2. Query Functions Updated
All student query functions now filter out soft-deleted records:

#### In `backend/db.py`:
- `get_all_students()` - filters `deleted_at=None`
- `get_student_by_id()` - filters `deleted_at=None`
- `get_student_by_student_id()` - filters `deleted_at=None`
- `delete_student()` - now sets `deleted_at` timestamp instead of deleting

#### In `backend/db_helpers.py`:
- `get_all_students()` - filters `deleted_at=None`
- `get_all_students_with_embeddings()` - filters `deleted_at=None`

#### In `backend/student_management_api.py`:
- `get_student_detail()` - filters `deleted_at=None`
- `update_student()` - filters `deleted_at=None` and validates roll numbers only against non-deleted students
- `delete_student()` - now soft deletes instead of hard deletes
- `get_student_embeddings()` - filters `deleted_at=None`

### 3. Migrations
- `backend/migrations/add_soft_delete_column.sql` - SQL migration script
- `backend/migrations/add_soft_delete.py` - Python migration script

## Benefits
✓ Student IDs can now be reused after deletion
✓ Complete audit trail - no data loss
✓ Attendance records remain intact for historical analysis
✓ Better data integrity and recovery options
✓ Complies with best practices for system design

## Backward Compatibility
- All queries automatically filter soft-deleted students
- Frontend doesn't need any changes
- API responses unchanged from user perspective

## Testing
To verify the fix works:
1. Register a student with ID "SP21-BCS-001"
2. Delete the student
3. Try to register a new student with the same ID "SP21-BCS-001"
4. The registration should now succeed
