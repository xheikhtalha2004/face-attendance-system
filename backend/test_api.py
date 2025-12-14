"""
Backend API Test Script
Tests all newly implemented endpoints
"""
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_health():
    """Test health check"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL.replace('/api', '')}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_get_courses():
    """Test get all courses"""
    print("\n=== Testing Get Courses ===")
    response = requests.get(f"{BASE_URL}/courses")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Courses found: {len(data)}")
    return response.status_code == 200

def test_get_students():
    """Test get all students"""
    print("\n=== Testing Get Students ===")
    response = requests.get(f"{BASE_URL}/students")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Students found: {len(data)}")
    return response.status_code == 200

def test_validate_student_id():
    """Test student ID validation"""
    print("\n=== Testing Student ID Validation ===")
    
    # Valid format
    response = requests.get(f"{BASE_URL}/register/validate-id/SP21-BCS-001")
    print(f"SP21-BCS-001: {response.json()}")
    
    # Invalid format
    response = requests.get(f"{BASE_URL}/register/validate-id/INVALID")
    print(f"INVALID: {response.json()}")
    
    return True

def test_get_enrollments():
    """Test enrollment endpoints"""
    print("\n=== Testing Get Enrollments ===")
    response = requests.get(f"{BASE_URL}/enrollments")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Enrollments found: {len(data)}")
    return response.status_code == 200

def test_get_active_session():
    """Test get active session"""
    print("\n=== Testing Get Active Session ===")
    response = requests.get(f"{BASE_URL}/sessions/active")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    return response.status_code == 200

def run_all_tests():
    """Run all backend tests"""
    print("="*60)
    print("BACKEND API TEST SUITE")
    print("="*60)
    
    tests = [
        ("Health Check", test_health),
        ("Get Courses", test_get_courses),
        ("Get Students", test_get_students),
        ("Student ID Validation", test_validate_student_id),
        ("Get Enrollments", test_get_enrollments),
        ("Get Active Session", test_get_active_session),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} FAILED: {str(e)}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    return passed == total

if __name__ == '__main__':
    print("Make sure backend server is running on http://localhost:5000")
    print("Press Enter to start tests...")
    input()
    
    success = run_all_tests()
    exit(0 if success else 1)
