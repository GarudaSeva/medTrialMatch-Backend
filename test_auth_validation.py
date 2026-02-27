import requests
import random

BASE_URL = "http://localhost:5000/api/auth"

def test_signup_validation():
    test_cases = [
        {
            "name": "Weak Password (no upper)",
            "data": {"username": "test", "email": f"test{random.randint(1,999)}@example.com", "password": "password123!"},
            "expected_status": 400
        },
        {
            "name": "Weak Password (no special)",
            "data": {"username": "test", "email": f"test{random.randint(1,999)}@example.com", "password": "Password123"},
            "expected_status": 400
        },
        {
            "name": "Invalid Email",
            "data": {"username": "test", "email": "invalid-email", "password": "Password123!"},
            "expected_status": 400
        },
        {
            "name": "Strong Password (Valid)",
            "data": {"username": "test_user", "email": f"valid{random.randint(1000,9999)}@example.com", "password": "StrongPassword123!"},
            "expected_status": 201
        }
    ]

    for case in test_cases:
        print(f"Testing: {case['name']}...")
        try:
            response = requests.post(f"{BASE_URL}/signup", json=case['data'])
            if response.status_code == case['expected_status']:
                print(f"✅ PASSED (Status {response.status_code})")
            else:
                print(f"❌ FAILED (Expected {case['expected_status']}, got {response.status_code})")
                print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_signup_validation()
