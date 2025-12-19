-- Add soft delete support to students table
-- This migration adds a deleted_at column to enable soft deletes
-- instead of hard deletes, allowing deleted student IDs to be reused

ALTER TABLE students ADD COLUMN deleted_at DATETIME DEFAULT NULL;

-- Create an index on deleted_at for faster queries filtering by this column
CREATE INDEX idx_students_deleted_at ON students(deleted_at);
