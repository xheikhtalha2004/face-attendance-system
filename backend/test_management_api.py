#!/usr/bin/env python3
"""
Quick API Testing Script
Test all new student and session management endpoints
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api"

def print_result(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"✅ {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def test_student_management():
    """Test student management endpoints"""
    print("\n" + "="*60)
    print("STUDENT MANAGEMENT TESTS")
    print("="*60)
    
    # 1. Get all students
    print("\n1. GET /api/students - List all students")
    response = requests.get(f"{BASE_URL}/students")
    print(f"   Status: {response.status_code}")
    students = response.json()
    print(f"   Total students: {len(students)}")
    
    if len(students) > 0:
        student_id = students[0]['id']
        student_name = students[0]['name']
        print(f"   First student: {student_name} (ID: {student_id})")
        
        # 2. Get student detail
        print(f"\n2. GET /api/students/{student_id} - Get student detail")
        response = requests.get(f"{BASE_URL}/students/{student_id}")
        print_result(f"Student Detail for {student_name}", response)
        
        # 3. Get student embeddings
        print(f"\n3. GET /api/students/{student_id}/embeddings - Get embeddings")
        response = requests.get(f"{BASE_URL}/students/{student_id}/embeddings")
        print_result("Student Embeddings", response)
        
        # 4. Get student attendance
        print(f"\n4. GET /api/students/{student_id}/attendance-records - Get attendance")
        response = requests.get(f"{BASE_URL}/students/{student_id}/attendance-records")
        print_result("Student Attendance Records", response)
        
        # 5. Update student
        print(f"\n5. PUT /api/students/{student_id} - Update student")
        update_data = {
            "name": f"{student_name} (Updated)",
            "email": "student@example.com",
            "phone": "+92-XXX-XXXXXXX"
        }
        response = requests.put(f"{BASE_URL}/students/{student_id}", json=update_data)
        print_result("Student Updated", response)

def test_session_management():
    """Test session management endpoints"""
    print("\n" + "="*60)
    print("SESSION MANAGEMENT TESTS")
    print("="*60)
    
    # 1. Get all sessions
    print("\n1. GET /api/sessions - List all sessions")
    response = requests.get(f"{BASE_URL}/sessions")
    print(f"   Status: {response.status_code}")
    sessions = response.json()
    print(f"   Total sessions: {len(sessions)}")
    
    # 2. Get courses for creating session
    print("\n2. GET /api/courses - Get courses")
    response = requests.get(f"{BASE_URL}/courses")
    print(f"   Status: {response.status_code}")
    courses = response.json()
    if len(courses) > 0:
        course = courses[0]
        print(f"   Using course: {course['courseId']} - {course['courseName']}")
        
        # 3. Create manual session
        print(f"\n3. POST /api/sessions/manual/create - Create manual session")
        now = datetime.now()
        start_time = now + timedelta(minutes=5)
        end_time = start_time + timedelta(hours=1)
        
        session_data = {
            "courseId": course['id'],
            "startsAt": start_time.isoformat(),
            "endsAt": end_time.isoformat()
        }
        response = requests.post(f"{BASE_URL}/sessions/manual/create", json=session_data)
        print_result("Session Created", response)
        
        if response.status_code == 201:
            session_id = response.json()['session']['id']
            
            # 4. Get session detail
            print(f"\n4. GET /api/sessions/{session_id} - Get session detail")
            response = requests.get(f"{BASE_URL}/sessions/{session_id}")
            print_result("Session Detail", response)
            
            # 5. Activate session
            print(f"\n5. PUT /api/sessions/{session_id}/activate - Activate session")
            response = requests.put(f"{BASE_URL}/sessions/{session_id}/activate")
            print_result("Session Activated", response)
            
            # 6. Get active sessions
            print(f"\n6. GET /api/sessions/active - Get active sessions")
            response = requests.get(f"{BASE_URL}/sessions/active")
            print_result("Active Sessions", response)
            
            # 7. End session
            print(f"\n7. PUT /api/sessions/{session_id}/end - End session")
            response = requests.put(f"{BASE_URL}/sessions/{session_id}/end")
            print_result("Session Ended", response)
    
    # 8. Verify data
    print(f"\n8. GET /api/sessions/verify-data - Verify data & timestamps")
    response = requests.get(f"{BASE_URL}/sessions/verify-data")
    print_result("Data Verification Report", response)
    
    # 9. Filter by status
    print(f"\n9. GET /api/sessions?status=COMPLETED - Filter by status")
    response = requests.get(f"{BASE_URL}/sessions?status=COMPLETED")
    print(f"   Status: {response.status_code}")
    print(f"   Completed sessions: {len(response.json())}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("FACE ATTENDANCE SYSTEM - API TEST SUITE")
    print("Testing Student & Session Management")
    print("="*60)
    
    try:
        test_student_management()
        test_session_management()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend server")
        print("   Make sure the backend is running on http://localhost:5000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
