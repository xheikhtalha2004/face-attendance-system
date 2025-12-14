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
        from db import create_course, create_or_update_time_slot, Course

        print("Starting database seeding...")

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
            },
            {
                'course_id': 'CS501',
                'course_name': 'Information Security',
                'professor_name': 'Dr. Omar Hassan',
                'description': 'Principles of cybersecurity, cryptography, and secure systems'
            },
            {
                'course_id': 'CS204',
                'course_name': 'Operating Systems',
                'professor_name': 'Prof. Layla Mahmoud',
                'description': 'Process management, memory management, and file systems'
            },
            {
                'course_id': 'CS205',
                'course_name': 'Computer Networks',
                'professor_name': 'Dr. Khalid Rahman',
                'description': 'Network protocols, TCP/IP, and network security'
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
                print(f"+ Created course: {course_data['course_name']} ({course_data['professor_name']})")
            else:
                created_courses[course_data['course_id']] = existing
                print(f"  Course already exists: {course_data['course_name']}")
        
        # Define weekly timetable (5 slots × 5 days, but skip some)
        # Slot times: 1(08:30-09:50), 2(09:50-11:10), 3(11:10-12:30), BREAK, 4(13:30-14:50), 5(14:50-16:10)
        timetable = [
            # Monday
            {'day': 'MONDAY', 'slot': 1, 'course': 'CS301', 'start': '08:30', 'end': '09:50', 'room': 'CS-101'},
            {'day': 'MONDAY', 'slot': 2, 'course': 'CS201', 'start': '09:50', 'end': '11:10', 'room': 'CS-102'},
            {'day': 'MONDAY', 'slot': 4, 'course': 'CS203', 'start': '13:30', 'end': '14:50', 'room': 'CS-103'},
            {'day': 'MONDAY', 'slot': 5, 'course': 'CS501', 'start': '14:50', 'end': '16:10', 'room': 'CS-104'},

            # Tuesday
            {'day': 'TUESDAY', 'slot': 1, 'course': 'CS202', 'start': '08:30', 'end': '09:50', 'room': 'CS-105'},
            {'day': 'TUESDAY', 'slot': 2, 'course': 'CS204', 'start': '09:50', 'end': '11:10', 'room': 'CS-101'},
            {'day': 'TUESDAY', 'slot': 3, 'course': 'CS401', 'start': '11:10', 'end': '12:30', 'room': 'CS-102'},
            {'day': 'TUESDAY', 'slot': 5, 'course': 'CS302', 'start': '14:50', 'end': '16:10', 'room': 'CS-103'},

            # Wednesday
            {'day': 'WEDNESDAY', 'slot': 1, 'course': 'CS205', 'start': '08:30', 'end': '09:50', 'room': 'CS-104'},
            {'day': 'WEDNESDAY', 'slot': 2, 'course': 'CS301', 'start': '09:50', 'end': '11:10', 'room': 'CS-105'},
            {'day': 'WEDNESDAY', 'slot': 3, 'course': 'CS101', 'start': '11:10', 'end': '12:30', 'room': 'CS-101'},
            {'day': 'WEDNESDAY', 'slot': 4, 'course': 'CS203', 'start': '13:30', 'end': '14:50', 'room': 'CS-102'},

            # Thursday
            {'day': 'THURSDAY', 'slot': 1, 'course': 'CS201', 'start': '08:30', 'end': '09:50', 'room': 'CS-103'},
            {'day': 'THURSDAY', 'slot': 2, 'course': 'CS202', 'start': '09:50', 'end': '11:10', 'room': 'CS-104'},
            {'day': 'THURSDAY', 'slot': 4, 'course': 'CS501', 'start': '13:30', 'end': '14:50', 'room': 'CS-105'},
            {'day': 'THURSDAY', 'slot': 5, 'course': 'CS401', 'start': '14:50', 'end': '16:10', 'room': 'CS-101'},

            # Friday
            {'day': 'FRIDAY', 'slot': 1, 'course': 'CS302', 'start': '08:30', 'end': '09:50', 'room': 'CS-102'},
            {'day': 'FRIDAY', 'slot': 2, 'course': 'CS204', 'start': '09:50', 'end': '11:10', 'room': 'CS-103'},
            {'day': 'FRIDAY', 'slot': 3, 'course': 'CS101', 'start': '11:10', 'end': '12:30', 'room': 'CS-104'},
            {'day': 'FRIDAY', 'slot': 4, 'course': 'CS205', 'start': '13:30', 'end': '14:50', 'room': 'CS-105'},
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
                    room=slot_data.get('room'),
                    late_threshold_minutes=5
                )
                print(f"+ Assigned {slot_data['day']} Slot {slot_data['slot']}: {course.course_name} in {slot_data.get('room', 'N/A')}")
        
        print("\n+ Database seeding completed successfully!")
        print(f"Total courses created/verified: {len(created_courses)}")
        print(f"Total time slots assigned: {len(timetable)}")


if __name__ == '__main__':
    seed_database()
