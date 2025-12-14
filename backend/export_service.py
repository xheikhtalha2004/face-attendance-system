"""
CSV Export Service
Generate CSV files for attendance reports
"""
import csv
import io
from datetime import datetime

def export_session_csv(session_id):
    """Export attendance for a specific session as CSV"""
    from db import get_session_by_id, get_attendance_by_session
    
    session = get_session_by_id(session_id)
    if not session:
        return None
    
    records = get_attendance_by_session(session_id)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'Student ID', 'Student Name', 'Status', 
        'Check-in Time', 'Confidence', 'Method', 'Notes'
    ])
    
    # Data rows
    for r in records:
        writer.writerow([
            r.student.student_id if r.student else '',
            r.student.name if r.student else '',
            r.status,
            r.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if r.check_in_time else '',
            f'{r.confidence:.2f}' if r.confidence else '',
            r.method,
            r.notes or ''
        ])
    
    output.seek(0)
    return output.getvalue()


def export_course_attendance_csv(course_id, date_from, date_to):
    """Export all attendance for a course in date range"""
    from db import Session, Attendance, db, Student
    
    # Get sessions  for this course in date range
    sessions = Session.query.filter(
        Session.course_id == course_id,
        Session.starts_at >= date_from,
        Session.starts_at <= date_to
    ).order_by(Session.starts_at).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'Session Date', 'Session Time', 'Student ID', 'Student Name', 
        'Status', 'Check-in Time', 'Method', 'Notes'
    ])
    
    # Data rows
    for session in sessions:
        from db import get_attendance_by_session
        attendance_records = get_attendance_by_session(session.id)
        
        for r in attendance_records:
            writer.writerow([
                session.starts_at.strftime('%Y-%m-%d'),
                session.starts_at.strftime('%H:%M'),
                r.student.student_id if r.student else '',
                r.student.name if r.student else '',
                r.status,
                r.check_in_time.strftime('%H:%M:%S') if r.check_in_time else '',
                r.method,
                r.notes or ''
            ])
    
    output.seek(0)
    return output.getvalue()
