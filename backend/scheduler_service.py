"""
Session Scheduler Service
Automatically creates sessions based on timetable and marks absentees
Uses APScheduler for background task execution
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging
import pytz

# Import DB functions
from db import (
    db, Session, TimeSlot, Course, Attendance, Student, Enrollment,
    get_active_slots_for_day, create_session, 
    get_sessions_by_date, mark_students_absent,
    get_attendance_by_session
)

logger = logging.getLogger(__name__)


class SessionSchedulerService:
    """
    Background service that checks for time slots and auto-creates sessions
    Also handles marking absentees after late threshold
    """
    
    def __init__(self, app):
        """
        Initialize scheduler service
        
        Args:
            app: Flask app instance (needed for app context)
        """
        self.app = app
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("Session Scheduler Service initialized")
    
    def start(self):
        """Start the scheduler jobs"""
        # Check for new sessions every minute
        self.scheduler.add_job(
            self.check_and_create_sessions,
            'interval',
            minutes=1,
            id='session_checker',
            replace_existing=True
        )
        # Activate any scheduled sessions that have reached their start time
        self.scheduler.add_job(
            self.activate_due_sessions,
            'interval',
            minutes=1,
            id='session_auto_activate',
            replace_existing=True
        )
        logger.info("Session checker scheduled (every 1 minute)")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Session Scheduler stopped")
    
    def check_and_create_sessions(self):
        """
        Check current time against timetable and create sessions if needed
        Called every minute by scheduler
        Only creates session once per slot per day
        """
        with self.app.app_context():
            try:
                now = datetime.now()
                current_day = now.strftime('%A').upper()  # MONDAY, TUESDAY, etc.
                current_time = now.time()
                
                # Get active time slots for today
                slots = get_active_slots_for_day(current_day)
                
                for slot in slots:
                    # Parse slot times
                    slot_start_time = datetime.strptime(slot.start_time, '%H:%M').time()
                    slot_end_time = datetime.strptime(slot.end_time, '%H:%M').time()
                    
                    # Check if we're within the slot time window
                    # Create session at start time (with 2-minute buffer)
                    time_diff = (datetime.combine(now.date(), current_time) - 
                                datetime.combine(now.date(), slot_start_time)).total_seconds()
                    
                    # Create session if we're within first 2 minutes of slot start
                    if 0 <= time_diff <= 120:  # 0-2 minutes after start
                        # Check if session already exists for this slot today
                        from db import Session
                        
                        today_start = datetime.combine(now.date(), slot_start_time)
                        today_end = datetime.combine(now.date(), slot_end_time)
                        
                        # Check for existing session for this time slot
                        existing_session = Session.query.filter(
                            Session.time_slot_id == slot.id,
                            db.func.date(Session.starts_at) == now.date(),
                            Session.status.in_(['ACTIVE', 'SCHEDULED'])
                        ).first()
                        
                        if existing_session:
                            logger.info(f"Session already exists for slot {slot.id} on {now.date()}")
                            continue
                        
                        # Create auto session
                        course = Course.query.get(slot.course_id)
                        
                        if course:
                            session = create_session(
                                course_id=slot.course_id,
                                starts_at=today_start,
                                ends_at=today_end,
                                time_slot_id=slot.id,
                                late_threshold_minutes=slot.late_threshold_minutes,
                                auto_created=True,
                                created_by=None
                            )
                            
                            logger.info(f"Auto-created session for {course.course_name} "
                                      f"at {slot.start_time} (Session ID: {session.id})")
                            
                            # Schedule absentee marking
                            self._schedule_mark_absentees(
                                session.id,
                                today_start + timedelta(minutes=slot.late_threshold_minutes + 5)
                            )
            
            except Exception as e:
                logger.error(f"Error in check_and_create_sessions: {str(e)}")
    
    def _schedule_mark_absentees(self, session_id, run_time):
        """
        Schedule marking absentees for a session
        
        Args:
            session_id: Session ID
            run_time: When to run (datetime)
        """
        try:
            self.scheduler.add_job(
                self.mark_absentees_for_session,
                'date',
                run_date=run_time,
                args=[session_id],
                id=f'mark_absent_{session_id}',
                replace_existing=True
            )
            logger.info(f"Scheduled absentee marking for session {session_id} at {run_time}")
        except Exception as e:
            logger.error(f"Error scheduling absentee marking: {str(e)}")

    def activate_due_sessions(self):
        """Auto-activate scheduled sessions that have reached their start time"""
        with self.app.app_context():
            try:
                now = datetime.utcnow()
                due_sessions = Session.query.filter(
                    Session.status == 'SCHEDULED',
                    Session.starts_at <= now,
                    Session.ends_at > now
                ).all()

                activated = 0
                for session in due_sessions:
                    session.status = 'ACTIVE'
                    activated += 1

                if activated:
                    db.session.commit()
                    logger.info(f"Auto-activated {activated} scheduled session(s)")
            except Exception as e:
                logger.error(f"Error auto-activating sessions: {str(e)}")
    
    def mark_absentees_for_session(self, session_id):
        """
        Mark all students without attendance as ABSENT
        
        Args:
            session_id: Session ID to process
        """
        with self.app.app_context():
            try:
                session = Session.query.get(session_id)
                if not session:
                    logger.warning(f"Session {session_id} not found")
                    return
                
                # Get enrolled students for the course
                enrolled = Enrollment.query.filter_by(course_id=session.course_id).all()
                enrolled_ids = [e.student_id for e in enrolled]
                
                # Get students with attendance in this session
                attendance_records = get_attendance_by_session(session_id)
                present_student_ids = set(a.student_id_fk for a in attendance_records)
                
                # Find absent students
                absent_student_ids = [sid for sid in enrolled_ids if sid not in present_student_ids]
                
                # Mark them absent
                if absent_student_ids:
                    marked = mark_students_absent(session_id, absent_student_ids)
                    logger.info(f"Marked {len(marked)} students as absent for session {session_id}")
                
                # Update session status to COMPLETED
                session.status = 'COMPLETED'
                db.session.commit()
                
                logger.info(f"Session {session_id} marked as COMPLETED")
                
            except Exception as e:
                logger.error(f"Error marking absentees for session {session_id}: {str(e)}")


# Global scheduler instance
_scheduler_service = None


def init_scheduler(app):
    """
    Initialize and start the scheduler service
    
    Args:
        app: Flask app instance
        
    Returns:
        SessionSchedulerService instance
    """
    global _scheduler_service
    
    if _scheduler_service is None:
        _scheduler_service = SessionSchedulerService(app)
        _scheduler_service.start()
        logger.info("Session scheduler service started")
    
    return _scheduler_service


def get_scheduler():
    """Get the global scheduler instance"""
    return _scheduler_service


def stop_scheduler():
    """Stop the scheduler service"""
    global _scheduler_service
    
    if _scheduler_service:
        _scheduler_service.stop()
        _scheduler_service = None
        logger.info("Session scheduler service stopped")
