"""
Database seed script for Face Attendance System
Populates courses and weekly timetable with sample data
"""
from app import app
from db import db

def seed_database():
    """Seed database with sample courses and timetable"""
    
    with app.app_context():
        # Import inside context
        from db import create_course, create_or_update_time_slot, User, Course
        from werkzeug.security import generate_password_hash
        
        print("Starting database seeding...")
        
        # Create default admin user if not exists
        admin = User.query.filter_by(email='admin@university.edu').first()
        if not admin:
            admin = User(
                email='admin@university.edu',
                password_hash=generate_password_hash('admin123'),
                name='System Administrator'
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ Created admin user (email: admin@university.edu, password: admin123)")
        
        # Define courses with Muslim teachers
        courses_data = [
            {
                'course_id': 'CS301',
                'course_name': 'Computer Vision',
                'professor_name': 'Dr. Ahmad Khan',
                'description': 'Introduction to image processing and computer vision techniques'
            },
            {
                'course_id': 'CS201',
                'course_name': 'Object Oriented Programming',
                'professor_name': 'Prof. Fatima Ali',
                'description': 'Advanced OOP concepts using Java and C++'
            },
            {
                'course_id': 'CS202',
                'course_name': 'Java Programming',
                'professor_name': 'Dr. Hassan Malik',
                'description': 'Enterprise Java development and frameworks'
            },
            {
                'course_id': 'CS203',
                'course_name': 'Data Structures & Algorithms',
                'professor_name': 'Prof. Ayesha Rahman',
                'description': 'Fundamental data structures and algorithm design'
            },
            {
                'course_id': 'CS401',
                'course_name': 'Parallel & Distributed Computing',
                'professor_name': 'Dr. Muhammad Tariq',
                'description': 'Concurrent programming and distributed systems'
            },
            {
                'course_id': 'CS302',
                'course_name': 'Database Systems',
                'professor_name': 'Dr. Zainab Ahmed',
                'description': 'Relational databases and SQL'
            },
            {
                'course_id': 'CS101',
                'course_name': 'Introduction to Programming',
                'professor_name': 'Prof. Ibrahim Yousaf',
                'description': 'Programming fundamentals using Python'
            }
        ]
        
        # Create courses
        created_courses = {}
        for course_data in courses_data:
            # Check if course already exists
            existing = Course.query.filter_by(course_id=course_data['course_id']).first()
            
            if not existing:
                course = create_course(**course_data)
                created_courses[course_data['course_id']] = course
                print(f"✓ Created course: {course_data['course_name']} ({course_data['professor_name']})")
            else:
                created_courses[course_data['course_id']] = existing
                print(f"  Course already exists: {course_data['course_name']}")
        
        # Define weekly timetable (5 slots × 5 days, but skip some)
        # Slot times: 1(08:30-09:50), 2(09:50-11:10), 3(11:10-12:30), BREAK, 4(13:30-14:50), 5(14:50-16:10)
        timetable = [
            # Monday
            {'day': 'MONDAY', 'slot': 1, 'course': 'CS301', 'start': '08:30', 'end': '09:50'},
            {'day': 'MONDAY', 'slot': 2, 'course': 'CS201', 'start': '09:50', 'end': '11:10'},
            {'day': 'MONDAY', 'slot': 4, 'course': 'CS203', 'start': '13:30', 'end': '14:50'},
            
            # Tuesday
            {'day': 'TUESDAY', 'slot': 1, 'course': 'CS202', 'start': '08:30', 'end': '09:50'},
            {'day': 'TUESDAY', 'slot': 3, 'course': 'CS401', 'start': '11:10', 'end': '12:30'},
            {'day': 'TUESDAY', 'slot': 5, 'course': 'CS302', 'start': '14:50', 'end': '16:10'},
            
            # Wednesday
            {'day': 'WEDNESDAY', 'slot': 2, 'course': 'CS301', 'start': '09:50', 'end': '11:10'},
            {'day': 'WEDNESDAY', 'slot': 3, 'course': 'CS101', 'start': '11:10', 'end': '12:30'},
            {'day': 'WEDNESDAY', 'slot': 4, 'course': 'CS203', 'start': '13:30', 'end': '14:50'},
            
            # Thursday
            {'day': 'THURSDAY', 'slot': 1, 'course': 'CS201', 'start': '08:30', 'end': '09:50'},
            {'day': 'THURSDAY', 'slot': 2, 'course': 'CS202', 'start': '09:50', 'end': '11:10'},
            {'day': 'THURSDAY', 'slot': 5, 'course': 'CS401', 'start': '14:50', 'end': '16:10'},
            
            # Friday
            {'day': 'FRIDAY', 'slot': 1, 'course': 'CS302', 'start': '08:30', 'end': '09:50'},
            {'day': 'FRIDAY', 'slot': 3, 'course': 'CS101', 'start': '11:10', 'end': '12:30'},
        ]
        
        # Create time slots
        for slot_data in timetable:
            course = created_courses.get(slot_data['course'])
            if course:
                create_or_update_time_slot(
                    day_of_week=slot_data['day'],
                    slot_number=slot_data['slot'],
                    course_id=course.id,
                    start_time=slot_data['start'],
                    end_time=slot_data['end'],
                    late_threshold_minutes=5
                )
                print(f"✓ Assigned {slot_data['day']} Slot {slot_data['slot']}: {course.course_name}")
        
        print("\n✅ Database seeding completed successfully!")
        print(f"Total courses created/verified: {len(created_courses)}")
        print(f"Total time slots assigned: {len(timetable)}")
        print("\nAdmin Login Credentials:")
        print("  Email: admin@university.edu")
        print("  Password: admin123")


if __name__ == '__main__':
    seed_database()
