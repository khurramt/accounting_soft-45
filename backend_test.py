#!/usr/bin/env python3
import requests
import json
import sys
import os
from datetime import datetime, timedelta
import decimal
from typing import Dict, Any, Optional, Tuple, List
import io

# Get the backend URL from the frontend .env file
def get_backend_url():
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                return line.strip().split('=')[1].strip('"\'')
    return None

BACKEND_URL = get_backend_url()
if not BACKEND_URL:
    print("Error: Could not find REACT_APP_BACKEND_URL in frontend/.env")
    sys.exit(1)

API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Set a timeout for all requests
TIMEOUT = 10  # seconds

# Global variables to store auth tokens and IDs
ACCESS_TOKEN = None
REFRESH_TOKEN = None
SESSION_ID = None
USER_ID = None
COMPANY_ID = None

# Custom JSON encoder to handle decimal values
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def pretty_print_json(data):
    """Print JSON data with proper formatting and decimal handling"""
    return json.dumps(data, indent=2, cls=DecimalEncoder)

def test_root_endpoint():
    """Test the root endpoint"""
    try:
        print("\n🔍 Testing root endpoint...")
        response = requests.get(f"{API_URL}/", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
            if "message" in data:
                print("✅ Root endpoint test passed")
                return True
            else:
                print(f"❌ Root endpoint test failed: Unexpected response")
                return False
        else:
            print(f"❌ Root endpoint test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Root endpoint test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Root endpoint test failed: {str(e)}")
        return False

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        print("\n🔍 Testing health endpoint...")
        response = requests.get(f"{API_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
            if "status" in data and data["status"] == "healthy":
                print("✅ Health endpoint test passed")
                return True
            else:
                print(f"❌ Health endpoint test failed: Unexpected response")
                return False
        else:
            print(f"❌ Health endpoint test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Health endpoint test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Health endpoint test failed: {str(e)}")
        return False

def test_login_demo_user():
    """Test login with demo user"""
    global ACCESS_TOKEN, REFRESH_TOKEN, USER_ID
    
    try:
        print("\n🔍 Testing login with demo user...")
        payload = {
            "email": "demo@quickbooks.com",
            "password": "Password123!",
            "device_info": {"browser": "python-requests", "os": "test-environment"},
            "remember_me": False
        }
        
        # Use requests with verify=False to bypass SSL verification
        response = requests.post(
            f"{API_URL}/auth/login", 
            json=payload, 
            timeout=TIMEOUT,
            verify=False  # Disable SSL verification
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "access_token" in data and "refresh_token" in data and "user" in data:
                ACCESS_TOKEN = data["access_token"]
                REFRESH_TOKEN = data["refresh_token"]
                USER_ID = data["user"]["user_id"]
                print("✅ Demo user login test passed")
                return True
            else:
                print(f"❌ Demo user login test failed: Unexpected response")
                return False
        else:
            print(f"❌ Demo user login test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Demo user login test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Demo user login test failed: {str(e)}")
        return False

def test_token_refresh():
    """Test token refresh functionality"""
    global ACCESS_TOKEN, REFRESH_TOKEN
    
    if not REFRESH_TOKEN:
        print("❌ Token refresh test skipped: No refresh token available")
        return False
    
    try:
        print("\n🔍 Testing token refresh...")
        payload = {
            "refresh_token": REFRESH_TOKEN
        }
        
        response = requests.post(f"{API_URL}/auth/refresh-token", json=payload, timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "access_token" in data and "refresh_token" in data:
                # Update tokens
                ACCESS_TOKEN = data["access_token"]
                REFRESH_TOKEN = data["refresh_token"]
                print("✅ Token refresh test passed")
                return True
            else:
                print(f"❌ Token refresh test failed: Unexpected response")
                return False
        else:
            print(f"❌ Token refresh test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Token refresh test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Token refresh test failed: {str(e)}")
        return False

def test_get_user_companies():
    """Test getting user companies"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN:
        print("❌ Get user companies test skipped: No access token available")
        return False
    
    try:
        print("\n🔍 Testing get user companies...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(f"{API_URL}/auth/companies", headers=headers, timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if isinstance(data, list):
                # Store company ID if available
                if len(data) > 0:
                    COMPANY_ID = data[0]["company"]["company_id"]
                    print(f"Using company ID: {COMPANY_ID}")
                print("✅ Get user companies test passed")
                return True
            else:
                print(f"❌ Get user companies test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get user companies test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get user companies test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get user companies test failed: {str(e)}")
        return False

def test_company_access():
    """Test company access"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Company access test skipped: No access token or company ID available")
        return False
    
    try:
        print(f"\n🔍 Testing company access for company ID: {COMPANY_ID}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.post(f"{API_URL}/auth/companies/{COMPANY_ID}/access", headers=headers, timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "message" in data and data.get("message") == "Company access granted":
                print("✅ Company access test passed")
                return True
            else:
                print(f"❌ Company access test failed: Unexpected response")
                return False
        else:
            print(f"❌ Company access test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Company access test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Company access test failed: {str(e)}")
        return False

# ===== ACCOUNTS API TESTS =====

def test_create_account():
    """Test creating an account"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create account test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create account...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique account name to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        payload = {
            "account_name": f"Test Account {timestamp}",
            "account_type": "assets",
            "description": "Test account created via API",
            "opening_balance": 1000.00
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/accounts/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "account_id" in data and data.get("account_name") == payload["account_name"]:
                account_id = data["account_id"]
                print(f"✅ Create account test passed (ID: {account_id})")
                return True, account_id
            else:
                print(f"❌ Create account test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create account test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create account test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create account test failed: {str(e)}")
        return False, None

def test_get_accounts():
    """Test getting accounts with pagination"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get accounts test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get accounts with pagination...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with pagination parameters
        params = {
            "page": 1,
            "page_size": 10,
            "sort_by": "account_name",
            "sort_order": "asc"
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/accounts/", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total" in data and "page" in data:
                print(f"✅ Get accounts test passed (Found {data['total']} accounts)")
                return True
            else:
                print(f"❌ Get accounts test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get accounts test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get accounts test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get accounts test failed: {str(e)}")
        return False

def test_get_account_by_id(account_id):
    """Test getting an account by ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not account_id:
        print("❌ Get account by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get account by ID: {account_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/accounts/{account_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "account_id" in data and data["account_id"] == account_id:
                print("✅ Get account by ID test passed")
                return True
            else:
                print(f"❌ Get account by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get account by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get account by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get account by ID test failed: {str(e)}")
        return False

def test_update_account(account_id):
    """Test updating an account"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not account_id:
        print("❌ Update account test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing update account: {account_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Updated account data
        payload = {
            "account_name": f"Updated Account {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "Updated description via API test"
        }
        
        response = requests.put(
            f"{API_URL}/companies/{COMPANY_ID}/accounts/{account_id}", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "account_id" in data and data["account_id"] == account_id and data["account_name"] == payload["account_name"]:
                print("✅ Update account test passed")
                return True
            else:
                print(f"❌ Update account test failed: Unexpected response")
                return False
        else:
            print(f"❌ Update account test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Update account test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Update account test failed: {str(e)}")
        return False

def test_delete_account(account_id):
    """Test deleting an account (soft delete)"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not account_id:
        print("❌ Delete account test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing delete account: {account_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.delete(
            f"{API_URL}/companies/{COMPANY_ID}/accounts/{account_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "message" in data and "deleted" in data["message"].lower():
                print("✅ Delete account test passed")
                return True
            else:
                print(f"❌ Delete account test failed: Unexpected response")
                return False
        else:
            print(f"❌ Delete account test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Delete account test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Delete account test failed: {str(e)}")
        return False

def test_merge_accounts(source_account_id, target_account_id):
    """Test merging accounts"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not source_account_id or not target_account_id:
        print("❌ Merge accounts test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing merge accounts: {source_account_id} into {target_account_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        params = {
            "target_account_id": target_account_id
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/accounts/{source_account_id}/merge", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "message" in data and "merged" in data["message"].lower():
                print("✅ Merge accounts test passed")
                return True
            else:
                print(f"❌ Merge accounts test failed: Unexpected response")
                return False
        else:
            print(f"❌ Merge accounts test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Merge accounts test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Merge accounts test failed: {str(e)}")
        return False

# ===== CUSTOMERS API TESTS =====

def test_create_customer():
    """Test creating a customer"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create customer test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create customer...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique customer name to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        payload = {
            "customer_name": f"Test Customer {timestamp}",
            "company_name": "Test Company LLC",
            "customer_type": "business",
            "first_name": "John",
            "last_name": "Doe",
            "email": f"test.customer.{timestamp}@example.com",
            "phone": "555-123-4567",
            "address_line1": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip_code": "12345",
            "country": "US"
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/customers/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "customer_id" in data and data.get("customer_name") == payload["customer_name"]:
                customer_id = data["customer_id"]
                print(f"✅ Create customer test passed (ID: {customer_id})")
                return True, customer_id
            else:
                print(f"❌ Create customer test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create customer test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create customer test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create customer test failed: {str(e)}")
        return False, None

def test_get_customers():
    """Test getting customers with filtering"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get customers test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get customers with filtering...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with filtering parameters
        params = {
            "page": 1,
            "page_size": 10,
            "sort_by": "customer_name",
            "sort_order": "asc",
            "is_active": True
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/customers/", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total" in data and "page" in data:
                print(f"✅ Get customers test passed (Found {data['total']} customers)")
                return True
            else:
                print(f"❌ Get customers test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get customers test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get customers test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get customers test failed: {str(e)}")
        return False

def test_get_customer_by_id(customer_id):
    """Test getting a customer by ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not customer_id:
        print("❌ Get customer by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get customer by ID: {customer_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/customers/{customer_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "customer_id" in data and data["customer_id"] == customer_id:
                print("✅ Get customer by ID test passed")
                return True
            else:
                print(f"❌ Get customer by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get customer by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get customer by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get customer by ID test failed: {str(e)}")
        return False

def test_update_customer(customer_id):
    """Test updating a customer"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not customer_id:
        print("❌ Update customer test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing update customer: {customer_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Updated customer data
        payload = {
            "customer_name": f"Updated Customer {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "phone": "555-987-6543",
            "address_line1": "456 Updated St"
        }
        
        response = requests.put(
            f"{API_URL}/companies/{COMPANY_ID}/customers/{customer_id}", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "customer_id" in data and data["customer_id"] == customer_id and data["customer_name"] == payload["customer_name"]:
                print("✅ Update customer test passed")
                return True
            else:
                print(f"❌ Update customer test failed: Unexpected response")
                return False
        else:
            print(f"❌ Update customer test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Update customer test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Update customer test failed: {str(e)}")
        return False

def test_delete_customer(customer_id):
    """Test deleting a customer (soft delete)"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not customer_id:
        print("❌ Delete customer test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing delete customer: {customer_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.delete(
            f"{API_URL}/companies/{COMPANY_ID}/customers/{customer_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "message" in data and "deleted" in data["message"].lower():
                print("✅ Delete customer test passed")
                return True
            else:
                print(f"❌ Delete customer test failed: Unexpected response")
                return False
        else:
            print(f"❌ Delete customer test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Delete customer test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Delete customer test failed: {str(e)}")
        return False

def test_get_customer_transactions(customer_id):
    """Test getting customer transactions"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not customer_id:
        print("❌ Get customer transactions test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get customer transactions: {customer_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/customers/{customer_id}/transactions", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "transactions" in data:
                print("✅ Get customer transactions test passed")
                return True
            else:
                print(f"❌ Get customer transactions test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get customer transactions test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get customer transactions test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get customer transactions test failed: {str(e)}")
        return False

def test_get_customer_balance(customer_id):
    """Test getting customer balance"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not customer_id:
        print("❌ Get customer balance test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get customer balance: {customer_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/customers/{customer_id}/balance", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "customer_id" in data and "balance" in data:
                print("✅ Get customer balance test passed")
                return True
            else:
                print(f"❌ Get customer balance test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get customer balance test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get customer balance test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get customer balance test failed: {str(e)}")
        return False

# ===== VENDORS API TESTS =====

def test_create_vendor():
    """Test creating a vendor"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create vendor test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create vendor...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique vendor name to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        payload = {
            "vendor_name": f"Test Vendor {timestamp}",
            "company_name": "Test Vendor Inc.",
            "vendor_type": "supplier",
            "contact_person": "Jane Smith",
            "email": f"test.vendor.{timestamp}@example.com",
            "phone": "555-987-6543",
            "address_line1": "789 Vendor St",
            "city": "Vendor City",
            "state": "VS",
            "zip_code": "54321",
            "country": "US",
            "eligible_1099": True
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/vendors/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "vendor_id" in data and data.get("vendor_name") == payload["vendor_name"]:
                vendor_id = data["vendor_id"]
                print(f"✅ Create vendor test passed (ID: {vendor_id})")
                return True, vendor_id
            else:
                print(f"❌ Create vendor test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create vendor test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create vendor test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create vendor test failed: {str(e)}")
        return False, None

def test_get_vendors():
    """Test getting vendors"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get vendors test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get vendors...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with filtering parameters
        params = {
            "page": 1,
            "page_size": 10,
            "sort_by": "vendor_name",
            "sort_order": "asc"
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/vendors/", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total" in data and "page" in data:
                print(f"✅ Get vendors test passed (Found {data['total']} vendors)")
                return True
            else:
                print(f"❌ Get vendors test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get vendors test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get vendors test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get vendors test failed: {str(e)}")
        return False

def test_get_vendor_by_id(vendor_id):
    """Test getting a vendor by ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not vendor_id:
        print("❌ Get vendor by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get vendor by ID: {vendor_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/vendors/{vendor_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "vendor_id" in data and data["vendor_id"] == vendor_id:
                print("✅ Get vendor by ID test passed")
                return True
            else:
                print(f"❌ Get vendor by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get vendor by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get vendor by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get vendor by ID test failed: {str(e)}")
        return False

def test_update_vendor(vendor_id):
    """Test updating a vendor"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not vendor_id:
        print("❌ Update vendor test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing update vendor: {vendor_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Updated vendor data
        payload = {
            "vendor_name": f"Updated Vendor {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "phone": "555-111-2222",
            "address_line1": "456 Updated Vendor St"
        }
        
        response = requests.put(
            f"{API_URL}/companies/{COMPANY_ID}/vendors/{vendor_id}", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "vendor_id" in data and data["vendor_id"] == vendor_id and data["vendor_name"] == payload["vendor_name"]:
                print("✅ Update vendor test passed")
                return True
            else:
                print(f"❌ Update vendor test failed: Unexpected response")
                return False
        else:
            print(f"❌ Update vendor test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Update vendor test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Update vendor test failed: {str(e)}")
        return False

def test_delete_vendor(vendor_id):
    """Test deleting a vendor (soft delete)"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not vendor_id:
        print("❌ Delete vendor test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing delete vendor: {vendor_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.delete(
            f"{API_URL}/companies/{COMPANY_ID}/vendors/{vendor_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "message" in data and "deleted" in data["message"].lower():
                print("✅ Delete vendor test passed")
                return True
            else:
                print(f"❌ Delete vendor test failed: Unexpected response")
                return False
        else:
            print(f"❌ Delete vendor test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Delete vendor test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Delete vendor test failed: {str(e)}")
        return False

def test_get_vendor_transactions(vendor_id):
    """Test getting vendor transactions"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not vendor_id:
        print("❌ Get vendor transactions test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get vendor transactions: {vendor_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/vendors/{vendor_id}/transactions", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "transactions" in data:
                print("✅ Get vendor transactions test passed")
                return True
            else:
                print(f"❌ Get vendor transactions test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get vendor transactions test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get vendor transactions test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get vendor transactions test failed: {str(e)}")
        return False

# ===== ITEMS API TESTS =====

def test_create_item():
    """Test creating an item"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create item test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create item...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique item name to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        payload = {
            "item_name": f"Test Item {timestamp}",
            "item_type": "inventory",
            "description": "Test item created via API",
            "sales_price": 49.99,
            "purchase_cost": 29.99,
            "quantity_on_hand": 10,
            "reorder_point": 25,
            "manufacturer": "Test Manufacturer"
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/items/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "item_id" in data and data.get("item_name") == payload["item_name"]:
                item_id = data["item_id"]
                print(f"✅ Create item test passed (ID: {item_id})")
                return True, item_id
            else:
                print(f"❌ Create item test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create item test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create item test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create item test failed: {str(e)}")
        return False, None

def test_get_items():
    """Test getting items"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get items test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get items...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with filtering parameters
        params = {
            "page": 1,
            "page_size": 10,
            "sort_by": "item_name",
            "sort_order": "asc"
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/items/", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total" in data and "page" in data:
                print(f"✅ Get items test passed (Found {data['total']} items)")
                return True
            else:
                print(f"❌ Get items test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get items test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get items test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get items test failed: {str(e)}")
        return False

def test_get_item_by_id(item_id):
    """Test getting an item by ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not item_id:
        print("❌ Get item by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get item by ID: {item_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/items/{item_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "item_id" in data and data["item_id"] == item_id:
                print("✅ Get item by ID test passed")
                return True
            else:
                print(f"❌ Get item by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get item by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get item by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get item by ID test failed: {str(e)}")
        return False

def test_update_item(item_id):
    """Test updating an item"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not item_id:
        print("❌ Update item test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing update item: {item_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Updated item data
        payload = {
            "item_name": f"Updated Item {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "Updated description via API test",
            "sales_price": 59.99,
            "quantity_on_hand": 75
        }
        
        response = requests.put(
            f"{API_URL}/companies/{COMPANY_ID}/items/{item_id}", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "item_id" in data and data["item_id"] == item_id and data["item_name"] == payload["item_name"]:
                print("✅ Update item test passed")
                return True
            else:
                print(f"❌ Update item test failed: Unexpected response")
                return False
        else:
            print(f"❌ Update item test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Update item test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Update item test failed: {str(e)}")
        return False

def test_delete_item(item_id):
    """Test deleting an item (soft delete)"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not item_id:
        print("❌ Delete item test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing delete item: {item_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.delete(
            f"{API_URL}/companies/{COMPANY_ID}/items/{item_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "message" in data and "deleted" in data["message"].lower():
                print("✅ Delete item test passed")
                return True
            else:
                print(f"❌ Delete item test failed: Unexpected response")
                return False
        else:
            print(f"❌ Delete item test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Delete item test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Delete item test failed: {str(e)}")
        return False

def test_get_low_stock_items():
    """Test getting low stock items"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get low stock items test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get low stock items...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/items/low-stock", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            print("✅ Get low stock items test passed")
            return True
        else:
            print(f"❌ Get low stock items test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get low stock items test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get low stock items test failed: {str(e)}")
        return False

# ===== COMPANY MANAGEMENT API TESTS =====

def test_list_companies():
    """Test listing companies for authenticated user"""
    global ACCESS_TOKEN
    
    if not ACCESS_TOKEN:
        print("❌ List companies test skipped: No access token available")
        return False
    
    try:
        print("\n🔍 Testing GET /api/companies - List companies...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if isinstance(data, list):
                print(f"✅ List companies test passed (Found {len(data)} companies)")
                return True
            else:
                print(f"❌ List companies test failed: Unexpected response")
                return False
        else:
            print(f"❌ List companies test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ List companies test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ List companies test failed: {str(e)}")
        return False

def test_create_company():
    """Test creating a new company"""
    global ACCESS_TOKEN
    
    if not ACCESS_TOKEN:
        print("❌ Create company test skipped: No access token available")
        return False, None
    
    try:
        print("\n🔍 Testing POST /api/companies - Create company...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique company name to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        payload = {
            "company_name": f"Test Company {timestamp}",
            "company_type": "corporation",
            "industry": "technology",
            "address_line1": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip_code": "12345",
            "country": "US",
            "phone": "555-123-4567",
            "email": f"test.company.{timestamp}@example.com",
            "website": "https://example.com",
            "fiscal_year_start": "01-01",
            "tax_year_start": "01-01",
            "currency": "USD",
            "language": "en-US"
        }
        
        response = requests.post(
            f"{API_URL}/companies/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 200 or response.status_code == 201:
            if "company_id" in data and data.get("company_name") == payload["company_name"]:
                company_id = data["company_id"]
                print(f"✅ Create company test passed (ID: {company_id})")
                return True, company_id
            else:
                print(f"❌ Create company test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create company test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create company test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create company test failed: {str(e)}")
        return False, None

def test_get_company_by_id(company_id):
    """Test getting company details by ID"""
    global ACCESS_TOKEN
    
    if not ACCESS_TOKEN or not company_id:
        print("❌ Get company by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing GET /api/companies/{company_id} - Get company details...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{company_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "company_id" in data and data["company_id"] == company_id:
                print("✅ Get company by ID test passed")
                return True
            else:
                print(f"❌ Get company by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get company by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get company by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get company by ID test failed: {str(e)}")
        return False

def test_update_company(company_id):
    """Test updating company information"""
    global ACCESS_TOKEN
    
    if not ACCESS_TOKEN or not company_id:
        print("❌ Update company test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing PUT /api/companies/{company_id} - Update company...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Updated company data
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        payload = {
            "company_name": f"Updated Company {timestamp}",
            "phone": "555-987-6543",
            "address_line1": "456 Updated St",
            "website": "https://updated-example.com"
        }
        
        response = requests.put(
            f"{API_URL}/companies/{company_id}", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "company_id" in data and data["company_id"] == company_id and data["company_name"] == payload["company_name"]:
                print("✅ Update company test passed")
                return True
            else:
                print(f"❌ Update company test failed: Unexpected response")
                return False
        else:
            print(f"❌ Update company test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Update company test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Update company test failed: {str(e)}")
        return False

def test_get_company_settings(company_id):
    """Test getting company settings"""
    global ACCESS_TOKEN
    
    if not ACCESS_TOKEN or not company_id:
        print("❌ Get company settings test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing GET /api/companies/{company_id}/settings - Get company settings...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{company_id}/settings", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if isinstance(data, list):
                print("✅ Get company settings test passed")
                return True
            else:
                print(f"❌ Get company settings test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get company settings test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get company settings test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get company settings test failed: {str(e)}")
        return False

def test_update_company_settings(company_id):
    """Test updating company settings"""
    global ACCESS_TOKEN
    
    if not ACCESS_TOKEN or not company_id:
        print("❌ Update company settings test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing PUT /api/companies/{company_id}/settings - Update company settings...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Settings to update
        payload = {
            "settings": [
                {
                    "category": "general",
                    "key": "default_currency",
                    "value": "USD"
                },
                {
                    "category": "general",
                    "key": "default_language",
                    "value": "en-US"
                },
                {
                    "category": "invoicing",
                    "key": "default_terms",
                    "value": "Net 30"
                }
            ]
        }
        
        response = requests.put(
            f"{API_URL}/companies/{company_id}/settings", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if isinstance(data, list):
                print("✅ Update company settings test passed")
                return True
            else:
                print(f"❌ Update company settings test failed: Unexpected response")
                return False
        else:
            print(f"❌ Update company settings test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Update company settings test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Update company settings test failed: {str(e)}")
        return False

def test_delete_company(company_id):
    """Test deleting a company"""
    global ACCESS_TOKEN
    
    if not ACCESS_TOKEN or not company_id:
        print("❌ Delete company test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing DELETE /api/companies/{company_id} - Delete company...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.delete(
            f"{API_URL}/companies/{company_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "message" in data and "deleted" in data["message"].lower():
                print("✅ Delete company test passed")
                return True
            else:
                print(f"❌ Delete company test failed: Unexpected response")
                return False
        else:
            print(f"❌ Delete company test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Delete company test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Delete company test failed: {str(e)}")
        return False

def run_company_management_tests():
    """Run all Company Management API tests"""
    print("\n🔍 Starting QuickBooks Clone Company Management API tests...")
    print(f"🕒 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results
    results = {}
    
    # Login and get access token
    results["login_demo_user"] = test_login_demo_user()
    if not results["login_demo_user"]:
        print("❌ Login failed, skipping all company management tests")
        return results
    
    # Test listing companies
    results["list_companies"] = test_list_companies()
    
    # Test creating a new company
    create_result, company_id = test_create_company()
    results["create_company"] = create_result
    
    if company_id:
        # Test getting company details
        results["get_company_by_id"] = test_get_company_by_id(company_id)
        
        # Test updating company
        results["update_company"] = test_update_company(company_id)
        
        # Test company settings
        results["get_company_settings"] = test_get_company_settings(company_id)
        results["update_company_settings"] = test_update_company_settings(company_id)
        
        # Test deleting company (do this last)
        results["delete_company"] = test_delete_company(company_id)
    else:
        print("❌ No company ID available, skipping company-specific tests")
    
    # Print summary
    print("\n📋 Company Management API Test Summary:")
    for test, result in results.items():
        status = "✅ Passed" if result else "❌ Failed"
        print(f"{test}: {status}")
    
    # Return overall success (all tests passed)
    return all(results.values())

# ===== EMPLOYEES API TESTS =====

def test_create_employee():
    """Test creating an employee"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create employee test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create employee...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique identifier to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        payload = {
            "first_name": "Test",
            "last_name": f"Employee {timestamp}",
            "email": f"test.employee.{timestamp}@example.com",
            "phone": "555-444-3333",
            "address_line1": "123 Employee St",
            "city": "Employee City",
            "state": "ES",
            "zip_code": "12345",
            "hire_date": "2023-01-15",
            "pay_type": "hourly",
            "hourly_rate": 25.50
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/employees/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "employee_id" in data and data.get("first_name") == payload["first_name"]:
                employee_id = data["employee_id"]
                print(f"✅ Create employee test passed (ID: {employee_id})")
                return True, employee_id
            else:
                print(f"❌ Create employee test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create employee test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create employee test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create employee test failed: {str(e)}")
        return False, None

def test_get_employees():
    """Test getting employees"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get employees test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get employees...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with filtering parameters
        params = {
            "page": 1,
            "page_size": 10,
            "sort_by": "last_name",
            "sort_order": "asc"
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/employees/", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total" in data and "page" in data:
                print(f"✅ Get employees test passed (Found {data['total']} employees)")
                return True
            else:
                print(f"❌ Get employees test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get employees test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get employees test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get employees test failed: {str(e)}")
        return False

def test_get_employee_by_id(employee_id):
    """Test getting an employee by ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not employee_id:
        print("❌ Get employee by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get employee by ID: {employee_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/employees/{employee_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "employee_id" in data and data["employee_id"] == employee_id:
                print("✅ Get employee by ID test passed")
                return True
            else:
                print(f"❌ Get employee by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get employee by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get employee by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get employee by ID test failed: {str(e)}")
        return False

def test_update_employee(employee_id):
    """Test updating an employee"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not employee_id:
        print("❌ Update employee test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing update employee: {employee_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Updated employee data
        payload = {
            "first_name": "Updated",
            "last_name": f"Employee {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "phone": "555-999-8888",
            "hourly_rate": 28.75
        }
        
        response = requests.put(
            f"{API_URL}/companies/{COMPANY_ID}/employees/{employee_id}", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "employee_id" in data and data["employee_id"] == employee_id and data["first_name"] == payload["first_name"]:
                print("✅ Update employee test passed")
                return True
            else:
                print(f"❌ Update employee test failed: Unexpected response")
                return False
        else:
            print(f"❌ Update employee test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Update employee test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Update employee test failed: {str(e)}")
        return False

def test_delete_employee(employee_id):
    """Test deleting an employee (soft delete)"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not employee_id:
        print("❌ Delete employee test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing delete employee: {employee_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.delete(
            f"{API_URL}/companies/{COMPANY_ID}/employees/{employee_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "message" in data and "deleted" in data["message"].lower():
                print("✅ Delete employee test passed")
                return True
            else:
                print(f"❌ Delete employee test failed: Unexpected response")
                return False
        else:
            print(f"❌ Delete employee test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Delete employee test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Delete employee test failed: {str(e)}")
        return False

def run_list_management_tests():
    """Run all List Management Module API tests"""
    print("\n🔍 Starting QuickBooks Clone List Management Module API tests...")
    print(f"🕒 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results
    results = {}
    
    # Login and get company access
    results["login_demo_user"] = test_login_demo_user()
    if results["login_demo_user"]:
        results["get_user_companies"] = test_get_user_companies()
        if COMPANY_ID:
            results["company_access"] = test_company_access()
        else:
            print("❌ No company ID available, skipping company-specific tests")
            return False
    else:
        print("❌ Login failed, skipping all other tests")
        return False
    
    # Test Accounts API
    print("\n📋 Testing Accounts API...")
    account_result, account_id = test_create_account()
    results["create_account"] = account_result
    
    # Create a second account for merge test
    account2_result, account2_id = test_create_account()
    results["create_account2"] = account2_result
    
    results["get_accounts"] = test_get_accounts()
    
    if account_id:
        results["get_account_by_id"] = test_get_account_by_id(account_id)
        results["update_account"] = test_update_account(account_id)
        
        if account2_id:
            results["merge_accounts"] = test_merge_accounts(account_id, account2_id)
        
        results["delete_account"] = test_delete_account(account_id)
    
    # Test Customers API
    print("\n📋 Testing Customers API...")
    customer_result, customer_id = test_create_customer()
    results["create_customer"] = customer_result
    
    results["get_customers"] = test_get_customers()
    
    if customer_id:
        results["get_customer_by_id"] = test_get_customer_by_id(customer_id)
        results["update_customer"] = test_update_customer(customer_id)
        results["get_customer_transactions"] = test_get_customer_transactions(customer_id)
        results["get_customer_balance"] = test_get_customer_balance(customer_id)
        results["delete_customer"] = test_delete_customer(customer_id)
    
    # Test Vendors API
    print("\n📋 Testing Vendors API...")
    vendor_result, vendor_id = test_create_vendor()
    results["create_vendor"] = vendor_result
    
    results["get_vendors"] = test_get_vendors()
    
    if vendor_id:
        results["get_vendor_by_id"] = test_get_vendor_by_id(vendor_id)
        results["update_vendor"] = test_update_vendor(vendor_id)
        results["get_vendor_transactions"] = test_get_vendor_transactions(vendor_id)
        results["delete_vendor"] = test_delete_vendor(vendor_id)
    
    # Test Items API
    print("\n📋 Testing Items API...")
    item_result, item_id = test_create_item()
    results["create_item"] = item_result
    
    results["get_items"] = test_get_items()
    results["get_low_stock_items"] = test_get_low_stock_items()
    
    if item_id:
        results["get_item_by_id"] = test_get_item_by_id(item_id)
        results["update_item"] = test_update_item(item_id)
        results["delete_item"] = test_delete_item(item_id)
    
    # Test Employees API
    print("\n📋 Testing Employees API...")
    employee_result, employee_id = test_create_employee()
    results["create_employee"] = employee_result
    
    results["get_employees"] = test_get_employees()
    
    if employee_id:
        results["get_employee_by_id"] = test_get_employee_by_id(employee_id)
        results["update_employee"] = test_update_employee(employee_id)
        results["delete_employee"] = test_delete_employee(employee_id)
    
    # Print summary
    print("\n📊 Test Summary:")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    print(f"\n🏁 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

# ===== TRANSACTION API TESTS =====

def test_create_invoice():
    """Test creating an invoice"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create invoice test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create invoice...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # First, create a customer for the invoice
        customer_success, customer_id = test_create_customer()
        if not customer_success or not customer_id:
            print("❌ Create invoice test failed: Could not create customer")
            return False, None
        
        # Create an item for the invoice line
        item_success, item_id = test_create_item()
        if not item_success or not item_id:
            print("❌ Create invoice test failed: Could not create item")
            return False, None
        
        # Generate a unique invoice
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create invoice payload
        payload = {
            "transaction_type": "invoice",
            "transaction_date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": (datetime.now().replace(day=1) + timedelta(days=30)).strftime("%Y-%m-%d"),
            "customer_id": customer_id,
            "memo": f"Test invoice created via API {timestamp}",
            "payment_terms": "Net 30",
            "billing_address": {
                "line1": "123 Billing St",
                "city": "Billing City",
                "state": "BC",
                "zip_code": "12345",
                "country": "US"
            },
            "shipping_address": {
                "line1": "456 Shipping St",
                "city": "Shipping City",
                "state": "SC",
                "zip_code": "54321",
                "country": "US"
            },
            "lines": [
                {
                    "line_number": 1,
                    "line_type": "item",
                    "item_id": item_id,
                    "description": "Test product",
                    "quantity": 2,
                    "unit_price": 100.00,
                    "tax_rate": 8.25
                },
                {
                    "line_number": 2,
                    "line_type": "item",
                    "description": "Additional service",
                    "quantity": 1,
                    "unit_price": 50.00,
                    "tax_rate": 8.25
                }
            ]
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/invoices/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "transaction_id" in data and data.get("transaction_type") == "invoice":
                invoice_id = data["transaction_id"]
                print(f"✅ Create invoice test passed (ID: {invoice_id})")
                return True, invoice_id
            else:
                print(f"❌ Create invoice test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create invoice test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create invoice test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create invoice test failed: {str(e)}")
        return False, None

def test_get_invoices():
    """Test getting invoices with filtering"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get invoices test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get invoices with filtering...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with filtering parameters
        params = {
            "page": 1,
            "page_size": 10,
            "sort_by": "transaction_date",
            "sort_order": "desc"
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/invoices/", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total" in data and "page" in data:
                print(f"✅ Get invoices test passed (Found {data['total']} invoices)")
                return True
            else:
                print(f"❌ Get invoices test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get invoices test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get invoices test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get invoices test failed: {str(e)}")
        return False

def test_get_invoice_by_id(invoice_id):
    """Test getting an invoice by ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not invoice_id:
        print("❌ Get invoice by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get invoice by ID: {invoice_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/invoices/{invoice_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "transaction_id" in data and data["transaction_id"] == invoice_id:
                print("✅ Get invoice by ID test passed")
                return True
            else:
                print(f"❌ Get invoice by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get invoice by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get invoice by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get invoice by ID test failed: {str(e)}")
        return False

def test_update_invoice(invoice_id):
    """Test updating an invoice"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not invoice_id:
        print("❌ Update invoice test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing update invoice: {invoice_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Updated invoice data
        payload = {
            "memo": f"Updated invoice memo {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "payment_terms": "Net 15"
        }
        
        response = requests.put(
            f"{API_URL}/companies/{COMPANY_ID}/invoices/{invoice_id}", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "transaction_id" in data and data["transaction_id"] == invoice_id and data["memo"] == payload["memo"]:
                print("✅ Update invoice test passed")
                return True
            else:
                print(f"❌ Update invoice test failed: Unexpected response")
                return False
        else:
            print(f"❌ Update invoice test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Update invoice test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Update invoice test failed: {str(e)}")
        return False

def test_post_invoice(invoice_id):
    """Test posting an invoice"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not invoice_id:
        print("❌ Post invoice test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing post invoice: {invoice_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        payload = {
            "posting_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/transactions/{invoice_id}/post", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "transaction_id" in data and data["transaction_id"] == invoice_id and data["is_posted"] == True:
                print("✅ Post invoice test passed")
                return True
            else:
                print(f"❌ Post invoice test failed: Unexpected response")
                return False
        else:
            print(f"❌ Post invoice test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Post invoice test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Post invoice test failed: {str(e)}")
        return False

def test_void_invoice(invoice_id):
    """Test voiding an invoice"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not invoice_id:
        print("❌ Void invoice test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing void invoice: {invoice_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        payload = {
            "reason": "Testing void functionality"
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/transactions/{invoice_id}/void", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "transaction_id" in data and data["transaction_id"] == invoice_id and data["is_void"] == True:
                print("✅ Void invoice test passed")
                return True
            else:
                print(f"❌ Void invoice test failed: Unexpected response")
                return False
        else:
            print(f"❌ Void invoice test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Void invoice test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Void invoice test failed: {str(e)}")
        return False

def test_create_bill():
    """Test creating a bill"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create bill test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create bill...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # First, create a vendor for the bill
        vendor_success, vendor_id = test_create_vendor()
        if not vendor_success or not vendor_id:
            print("❌ Create bill test failed: Could not create vendor")
            return False, None
        
        # Create an item for the bill line
        item_success, item_id = test_create_item()
        if not item_success or not item_id:
            print("❌ Create bill test failed: Could not create item")
            return False, None
        
        # Generate a unique bill
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create bill payload
        payload = {
            "transaction_type": "bill",
            "transaction_date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": (datetime.now().replace(day=1) + timedelta(days=30)).strftime("%Y-%m-%d"),
            "vendor_id": vendor_id,
            "memo": f"Test bill created via API {timestamp}",
            "payment_terms": "Net 30",
            "lines": [
                {
                    "line_number": 1,
                    "line_type": "item",
                    "item_id": item_id,
                    "description": "Test product purchase",
                    "quantity": 5,
                    "unit_price": 80.00
                },
                {
                    "line_number": 2,
                    "line_type": "account",
                    "description": "Consulting services",
                    "quantity": 1,
                    "unit_price": 200.00
                }
            ]
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/bills/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "transaction_id" in data and data.get("transaction_type") == "bill":
                bill_id = data["transaction_id"]
                print(f"✅ Create bill test passed (ID: {bill_id})")
                return True, bill_id
            else:
                print(f"❌ Create bill test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create bill test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create bill test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create bill test failed: {str(e)}")
        return False, None

def test_get_bills():
    """Test getting bills with filtering"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get bills test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get bills with filtering...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with filtering parameters
        params = {
            "page": 1,
            "page_size": 10,
            "sort_by": "transaction_date",
            "sort_order": "desc"
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/bills/", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total" in data and "page" in data:
                print(f"✅ Get bills test passed (Found {data['total']} bills)")
                return True
            else:
                print(f"❌ Get bills test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get bills test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get bills test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get bills test failed: {str(e)}")
        return False

def test_get_bill_by_id(bill_id):
    """Test getting a bill by ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not bill_id:
        print("❌ Get bill by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get bill by ID: {bill_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/bills/{bill_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "transaction_id" in data and data["transaction_id"] == bill_id:
                print("✅ Get bill by ID test passed")
                return True
            else:
                print(f"❌ Get bill by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get bill by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get bill by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get bill by ID test failed: {str(e)}")
        return False

def test_post_bill(bill_id):
    """Test posting a bill"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not bill_id:
        print("❌ Post bill test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing post bill: {bill_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        payload = {
            "posting_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/transactions/{bill_id}/post", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "transaction_id" in data and data["transaction_id"] == bill_id and data["is_posted"] == True:
                print("✅ Post bill test passed")
                return True
            else:
                print(f"❌ Post bill test failed: Unexpected response")
                return False
        else:
            print(f"❌ Post bill test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Post bill test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Post bill test failed: {str(e)}")
        return False

def test_create_payment():
    """Test creating a payment and applying it to an invoice"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create payment test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create payment...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # First, create an invoice to apply payment to
        invoice_success, invoice_id = test_create_invoice()
        if not invoice_success or not invoice_id:
            print("❌ Create payment test failed: Could not create invoice")
            return False, None
        
        # Post the invoice
        post_success = test_post_invoice(invoice_id)
        if not post_success:
            print("❌ Create payment test failed: Could not post invoice")
            return False, None
        
        # Get the invoice to determine amount
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/invoices/{invoice_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            print(f"❌ Create payment test failed: Could not get invoice details")
            return False, None
        
        invoice_data = response.json()
        invoice_amount = float(invoice_data.get("total_amount", 0))
        customer_id = invoice_data.get("customer_id")
        
        # Create an account for deposit
        account_success, account_id = test_create_account()
        if not account_success or not account_id:
            print("❌ Create payment test failed: Could not create deposit account")
            return False, None
        
        # Generate a unique payment
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create payment payload
        payload = {
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "payment_type": "check",
            "payment_method": "Check #12345",
            "reference_number": f"REF-{timestamp}",
            "customer_id": customer_id,
            "amount_received": invoice_amount,
            "deposit_to_account_id": account_id,
            "memo": f"Payment for invoice {invoice_id}",
            "applications": [
                {
                    "transaction_id": invoice_id,
                    "amount_applied": invoice_amount,
                    "discount_taken": 0
                }
            ]
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/payments/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "payment_id" in data:
                payment_id = data["payment_id"]
                print(f"✅ Create payment test passed (ID: {payment_id})")
                return True, payment_id
            else:
                print(f"❌ Create payment test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create payment test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create payment test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create payment test failed: {str(e)}")
        return False, None

def test_check_invoice_balance(invoice_id):
    """Test checking invoice balance after payment"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not invoice_id:
        print("❌ Check invoice balance test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing check invoice balance after payment: {invoice_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/invoices/{invoice_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "transaction_id" in data and data["transaction_id"] == invoice_id:
                balance_due = float(data.get("balance_due", 0))
                if balance_due == 0:
                    print("✅ Check invoice balance test passed - Balance is zero after payment")
                    return True
                else:
                    print(f"❌ Check invoice balance test failed: Balance due is {balance_due}, expected 0")
                    return False
            else:
                print(f"❌ Check invoice balance test failed: Unexpected response")
                return False
        else:
            print(f"❌ Check invoice balance test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Check invoice balance test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Check invoice balance test failed: {str(e)}")
        return False

def run_transaction_tests():
    """Run all Transaction Module API tests"""
    print("\n🔍 Starting QuickBooks Clone Transaction Module API tests...")
    print(f"🕒 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results
    results = {}
    
    # Login and get company access
    results["login_demo_user"] = test_login_demo_user()
    if results["login_demo_user"]:
        results["get_user_companies"] = test_get_user_companies()
        if COMPANY_ID:
            results["company_access"] = test_company_access()
        else:
            print("❌ No company ID available, skipping company-specific tests")
            return False
    else:
        print("❌ Login failed, skipping all other tests")
        return False
    
    # Test Transaction Engine APIs
    print("\n📋 Testing Transaction Engine APIs...")
    
    # Test Invoice Creation
    invoice_result, invoice_id = test_create_invoice()
    results["create_invoice"] = invoice_result
    
    # Test Bill Creation
    bill_result, bill_id = test_create_bill()
    results["create_bill"] = bill_result
    
    # Test Payment Creation
    payment_result, payment_id = test_create_payment()
    results["create_payment"] = payment_result
    
    # Test General Transaction Creation
    transaction_result, transaction_id = test_create_transaction()
    results["create_transaction"] = transaction_result
    
    # Test Sales Receipt Creation
    receipt_result, receipt_id = test_create_sales_receipt()
    results["create_sales_receipt"] = receipt_result
    
    # Test Invoice API
    print("\n📋 Testing Invoice API...")
    results["get_invoices"] = test_get_invoices()
    
    if invoice_id:
        results["get_invoice_by_id"] = test_get_invoice_by_id(invoice_id)
        results["update_invoice"] = test_update_invoice(invoice_id)
        results["post_invoice"] = test_post_invoice(invoice_id)
    
    # Test Bill API
    print("\n📋 Testing Bill API...")
    bill_result, bill_id = test_create_bill()
    results["create_bill"] = bill_result
    
    results["get_bills"] = test_get_bills()
    
    if bill_id:
        results["get_bill_by_id"] = test_get_bill_by_id(bill_id)
        results["post_bill"] = test_post_bill(bill_id)
    
    # Test Payment API
    print("\n📋 Testing Payment API...")
    # Create a new invoice for payment testing
    payment_invoice_result, payment_invoice_id = test_create_invoice()
    results["create_payment_invoice"] = payment_invoice_result
    
    if payment_invoice_id:
        results["post_payment_invoice"] = test_post_invoice(payment_invoice_id)
        payment_result, payment_id = test_create_payment()
        results["create_payment"] = payment_result
        
        if payment_result:
            results["check_invoice_balance"] = test_check_invoice_balance(payment_invoice_id)
    
    # Test voiding a transaction
    if invoice_id:
        # Create a new invoice for void testing
        void_invoice_result, void_invoice_id = test_create_invoice()
        results["create_void_invoice"] = void_invoice_result
        
        if void_invoice_id:
            results["post_void_invoice"] = test_post_invoice(void_invoice_id)
            results["void_invoice"] = test_void_invoice(void_invoice_id)
    
    # Print summary
    print("\n📊 Transaction Tests Summary:")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    print(f"\n🏁 Overall Transaction Tests Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

def run_banking_integration_tests():
    """Run all Banking Integration Module API tests"""
    print("\n🔍 Starting QuickBooks Clone Banking Integration Module API tests...")
    print(f"🕒 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results
    results = {}
    
    # Login and get company access
    results["login_demo_user"] = test_login_demo_user()
    if results["login_demo_user"]:
        results["get_user_companies"] = test_get_user_companies()
        if COMPANY_ID:
            results["company_access"] = test_company_access()
        else:
            print("❌ No company ID available, skipping banking tests")
            return False
    else:
        print("❌ Login failed, skipping all banking tests")
        return False
    
    # Test Banking Integration APIs
    print("\n📋 Testing Banking Integration APIs...")
    
    # Test Bank Connection Management
    print("\n🏦 Testing Bank Connection Management...")
    connection_result, connection_id = test_create_bank_connection()
    results["create_bank_connection"] = connection_result
    
    results["get_bank_connections"] = test_get_bank_connections()
    
    if connection_id:
        results["get_bank_connection_by_id"] = test_get_bank_connection_by_id(connection_id)
        results["update_bank_connection"] = test_update_bank_connection(connection_id)
        results["sync_bank_connection"] = test_sync_bank_connection(connection_id)
        results["get_bank_transactions_by_connection"] = test_get_bank_transactions_by_connection(connection_id)
    
    # Test Bank Transaction Management
    print("\n💳 Testing Bank Transaction Management...")
    results["get_bank_transactions"] = test_get_bank_transactions()
    
    # Test Institution Search
    print("\n🏛️ Testing Institution Search...")
    results["search_institutions"] = test_search_institutions()
    results["get_institution_by_id"] = test_get_institution_by_id()
    
    # Test File Upload
    print("\n📄 Testing File Upload...")
    results["upload_bank_statement"] = test_upload_bank_statement()
    
    # Clean up - delete the test connection
    if connection_id:
        results["delete_bank_connection"] = test_delete_bank_connection(connection_id)
    
    # Print summary
    print("\n📊 Banking Integration Module Test Summary:")
    for test_name, result in results.items():
        status = "✅ Passed" if result else "❌ Failed"
        print(f"{test_name}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All Banking Integration Module tests passed!")
    else:
        print("\n❌ Some Banking Integration Module tests failed.")
    
    return all_passed

if __name__ == "__main__":
    # Run the appropriate test suite based on command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "transactions":
            success = run_transaction_tests()
        elif sys.argv[1] == "banking":
            success = run_banking_integration_tests()
        elif sys.argv[1] == "companies":
            success = run_company_management_tests()
        else:
            print(f"Unknown test suite: {sys.argv[1]}")
            print("Available test suites: transactions, banking, companies")
            print("Usage: python backend_test.py [transactions|banking|companies]")
            print("If no argument is provided, list_management_tests will run by default")
            success = False
    else:
        success = run_list_management_tests()
    
    sys.exit(0 if success else 1)
# ===== INVENTORY MANAGEMENT TESTS =====

def test_inventory_overview():
    """Test getting inventory overview"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Inventory overview test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing inventory overview...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory/", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "total_items" in data and "total_value" in data:
                print("✅ Inventory overview test passed")
                return True
            else:
                print(f"❌ Inventory overview test failed: Unexpected response")
                return False
        else:
            print(f"❌ Inventory overview test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Inventory overview test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Inventory overview test failed: {str(e)}")
        return False

def test_get_low_stock_items():
    """Test getting low stock items"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get low stock items test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get low stock items...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory/low-stock", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            print(f"✅ Get low stock items test passed (Found {len(data)} items)")
            return True
        else:
            print(f"❌ Get low stock items test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get low stock items test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get low stock items test failed: {str(e)}")
        return False

def test_create_inventory_location():
    """Test creating an inventory location"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create inventory location test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create inventory location...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique location name to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        payload = {
            "location_name": f"Test Location {timestamp}",
            "location_type": "warehouse",
            "address": {
                "address_line1": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "zip_code": "12345",
                "country": "US"
            },
            "is_default": False,
            "allow_negative_stock": True
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-locations/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "location_id" in data and data.get("location_name") == payload["location_name"]:
                location_id = data["location_id"]
                print(f"✅ Create inventory location test passed (ID: {location_id})")
                return True, location_id
            else:
                print(f"❌ Create inventory location test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create inventory location test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create inventory location test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create inventory location test failed: {str(e)}")
        return False, None

def test_get_inventory_locations():
    """Test getting inventory locations"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get inventory locations test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get inventory locations...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-locations/", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if isinstance(data, list):
                print(f"✅ Get inventory locations test passed (Found {len(data)} locations)")
                return True
            else:
                print(f"❌ Get inventory locations test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get inventory locations test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get inventory locations test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get inventory locations test failed: {str(e)}")
        return False

def test_update_inventory_location(location_id):
    """Test updating an inventory location"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not location_id:
        print("❌ Update inventory location test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing update inventory location: {location_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Updated location data
        payload = {
            "location_name": f"Updated Location {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "manager_name": "Test Manager",
            "phone": "555-123-4567"
        }
        
        response = requests.put(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-locations/{location_id}", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "location_id" in data and data["location_id"] == location_id and data["location_name"] == payload["location_name"]:
                print("✅ Update inventory location test passed")
                return True
            else:
                print(f"❌ Update inventory location test failed: Unexpected response")
                return False
        else:
            print(f"❌ Update inventory location test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Update inventory location test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Update inventory location test failed: {str(e)}")
        return False

def test_create_inventory_adjustment():
    """Test creating an inventory adjustment"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create inventory adjustment test skipped: No access token or company ID available")
        return False, None
    
    # First, get an item to adjust
    try:
        print("\n🔍 Getting an item for inventory adjustment...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/items/", 
            headers=headers,
            params={"page": 1, "page_size": 1},
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get items: Status code {response.status_code}")
            return False, None
        
        data = response.json()
        if not data.get("items") or len(data["items"]) == 0:
            print("❌ No items found to adjust")
            return False, None
        
        item_id = data["items"][0]["item_id"]
        print(f"Found item ID: {item_id}")
        
        # Now create the adjustment
        print("\n🔍 Testing create inventory adjustment...")
        
        payload = {
            "item_id": item_id,
            "adjustment_date": datetime.now().strftime("%Y-%m-%d"),
            "adjustment_type": "quantity",
            "quantity_adjustment": 10,
            "unit_cost": 25.00,
            "reason_code": "test",
            "memo": "Test adjustment via API"
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-adjustments/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "adjustment_id" in data:
                adjustment_id = data["adjustment_id"]
                print(f"✅ Create inventory adjustment test passed (ID: {adjustment_id})")
                return True, adjustment_id
            else:
                print(f"❌ Create inventory adjustment test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create inventory adjustment test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create inventory adjustment test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create inventory adjustment test failed: {str(e)}")
        return False, None

def test_get_inventory_adjustments():
    """Test getting inventory adjustments"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get inventory adjustments test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get inventory adjustments...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with pagination parameters
        params = {
            "page": 1,
            "page_size": 10,
            "sort_by": "adjustment_date",
            "sort_order": "desc"
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-adjustments/", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total" in data:
                print(f"✅ Get inventory adjustments test passed (Found {data['total']} adjustments)")
                return True
            else:
                print(f"❌ Get inventory adjustments test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get inventory adjustments test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get inventory adjustments test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get inventory adjustments test failed: {str(e)}")
        return False

def test_get_adjustment_by_id(adjustment_id):
    """Test getting an adjustment by ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not adjustment_id:
        print("❌ Get adjustment by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get adjustment by ID: {adjustment_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-adjustments/{adjustment_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "adjustment_id" in data and data["adjustment_id"] == adjustment_id:
                print("✅ Get adjustment by ID test passed")
                return True
            else:
                print(f"❌ Get adjustment by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get adjustment by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get adjustment by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get adjustment by ID test failed: {str(e)}")
        return False

def test_create_purchase_order():
    """Test creating a purchase order"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create purchase order test skipped: No access token or company ID available")
        return False, None
    
    # First, get a vendor and an item
    try:
        print("\n🔍 Getting a vendor for purchase order...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        vendor_response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/vendors/", 
            headers=headers,
            params={"page": 1, "page_size": 1},
            timeout=TIMEOUT
        )
        
        if vendor_response.status_code != 200:
            print(f"❌ Failed to get vendors: Status code {vendor_response.status_code}")
            return False, None
        
        vendor_data = vendor_response.json()
        if not vendor_data.get("items") or len(vendor_data["items"]) == 0:
            print("❌ No vendors found for purchase order")
            return False, None
        
        vendor_id = vendor_data["items"][0]["vendor_id"]
        print(f"Found vendor ID: {vendor_id}")
        
        # Get an item
        item_response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/items/", 
            headers=headers,
            params={"page": 1, "page_size": 1},
            timeout=TIMEOUT
        )
        
        if item_response.status_code != 200:
            print(f"❌ Failed to get items: Status code {item_response.status_code}")
            return False, None
        
        item_data = item_response.json()
        if not item_data.get("items") or len(item_data["items"]) == 0:
            print("❌ No items found for purchase order")
            return False, None
        
        item_id = item_data["items"][0]["item_id"]
        print(f"Found item ID: {item_id}")
        
        # Now create the purchase order
        print("\n🔍 Testing create purchase order...")
        
        payload = {
            "vendor_id": vendor_id,
            "po_date": datetime.now().strftime("%Y-%m-%d"),
            "expected_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "memo": "Test purchase order via API",
            "lines": [
                {
                    "item_id": item_id,
                    "description": "Test item",
                    "quantity_ordered": 5,
                    "unit_cost": 20.00
                }
            ]
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/purchase-orders/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "purchase_order_id" in data:
                po_id = data["purchase_order_id"]
                print(f"✅ Create purchase order test passed (ID: {po_id})")
                return True, po_id
            else:
                print(f"❌ Create purchase order test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create purchase order test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create purchase order test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create purchase order test failed: {str(e)}")
        return False, None

def test_get_purchase_orders():
    """Test getting purchase orders"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get purchase orders test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get purchase orders...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with pagination parameters
        params = {
            "page": 1,
            "page_size": 10,
            "sort_by": "po_date",
            "sort_order": "desc"
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/purchase-orders/", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total" in data:
                print(f"✅ Get purchase orders test passed (Found {data['total']} purchase orders)")
                return True
            else:
                print(f"❌ Get purchase orders test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get purchase orders test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get purchase orders test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get purchase orders test failed: {str(e)}")
        return False

def test_get_purchase_order_by_id(po_id):
    """Test getting a purchase order by ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not po_id:
        print("❌ Get purchase order by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get purchase order by ID: {po_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/purchase-orders/{po_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "purchase_order_id" in data and data["purchase_order_id"] == po_id:
                print("✅ Get purchase order by ID test passed")
                return True
            else:
                print(f"❌ Get purchase order by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get purchase order by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get purchase order by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get purchase order by ID test failed: {str(e)}")
        return False

def test_update_purchase_order(po_id):
    """Test updating a purchase order"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not po_id:
        print("❌ Update purchase order test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing update purchase order: {po_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Updated purchase order data
        payload = {
            "memo": f"Updated memo {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "reference_number": "REF-123"
        }
        
        response = requests.put(
            f"{API_URL}/companies/{COMPANY_ID}/purchase-orders/{po_id}", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "purchase_order_id" in data and data["purchase_order_id"] == po_id and data["memo"] == payload["memo"]:
                print("✅ Update purchase order test passed")
                return True
            else:
                print(f"❌ Update purchase order test failed: Unexpected response")
                return False
        else:
            print(f"❌ Update purchase order test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Update purchase order test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Update purchase order test failed: {str(e)}")
        return False

def test_create_inventory_receipt(po_id=None):
    """Test creating an inventory receipt"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create inventory receipt test skipped: No access token or company ID available")
        return False, None
    
    # First, get a vendor and an item if no PO is provided
    try:
        print("\n🔍 Setting up for inventory receipt...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        vendor_id = None
        item_id = None
        
        if po_id:
            # Get PO details to use the same vendor and items
            po_response = requests.get(
                f"{API_URL}/companies/{COMPANY_ID}/purchase-orders/{po_id}", 
                headers=headers,
                timeout=TIMEOUT
            )
            
            if po_response.status_code == 200:
                po_data = po_response.json()
                vendor_id = po_data.get("vendor_id")
                if po_data.get("lines") and len(po_data["lines"]) > 0:
                    po_line = po_data["lines"][0]
                    item_id = po_line.get("item_id")
                    po_line_id = po_line.get("po_line_id")
                    print(f"Using vendor ID: {vendor_id}, item ID: {item_id}, PO line ID: {po_line_id}")
                else:
                    print("❌ No lines found in purchase order")
                    po_id = None  # Reset to get new vendor and item
            else:
                print(f"❌ Failed to get purchase order: Status code {po_response.status_code}")
                po_id = None  # Reset to get new vendor and item
        
        if not vendor_id:
            # Get a vendor
            vendor_response = requests.get(
                f"{API_URL}/companies/{COMPANY_ID}/vendors/", 
                headers=headers,
                params={"page": 1, "page_size": 1},
                timeout=TIMEOUT
            )
            
            if vendor_response.status_code != 200:
                print(f"❌ Failed to get vendors: Status code {vendor_response.status_code}")
                return False, None
            
            vendor_data = vendor_response.json()
            if not vendor_data.get("items") or len(vendor_data["items"]) == 0:
                print("❌ No vendors found for inventory receipt")
                return False, None
            
            vendor_id = vendor_data["items"][0]["vendor_id"]
            print(f"Found vendor ID: {vendor_id}")
        
        if not item_id:
            # Get an item
            item_response = requests.get(
                f"{API_URL}/companies/{COMPANY_ID}/items/", 
                headers=headers,
                params={"page": 1, "page_size": 1},
                timeout=TIMEOUT
            )
            
            if item_response.status_code != 200:
                print(f"❌ Failed to get items: Status code {item_response.status_code}")
                return False, None
            
            item_data = item_response.json()
            if not item_data.get("items") or len(item_data["items"]) == 0:
                print("❌ No items found for inventory receipt")
                return False, None
            
            item_id = item_data["items"][0]["item_id"]
            print(f"Found item ID: {item_id}")
        
        # Now create the inventory receipt
        print("\n🔍 Testing create inventory receipt...")
        
        receipt_lines = []
        if po_id and 'po_line_id' in locals():
            receipt_lines.append({
                "item_id": item_id,
                "po_line_id": po_line_id,
                "quantity_received": 2,
                "unit_cost": 20.00
            })
        else:
            receipt_lines.append({
                "item_id": item_id,
                "quantity_received": 2,
                "unit_cost": 20.00
            })
        
        payload = {
            "vendor_id": vendor_id,
            "purchase_order_id": po_id if po_id else None,
            "receipt_date": datetime.now().strftime("%Y-%m-%d"),
            "vendor_invoice_number": f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "memo": "Test inventory receipt via API",
            "lines": receipt_lines
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-receipts/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "receipt_id" in data:
                receipt_id = data["receipt_id"]
                print(f"✅ Create inventory receipt test passed (ID: {receipt_id})")
                return True, receipt_id
            else:
                print(f"❌ Create inventory receipt test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create inventory receipt test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create inventory receipt test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create inventory receipt test failed: {str(e)}")
        return False, None

def test_get_inventory_receipts():
    """Test getting inventory receipts"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get inventory receipts test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get inventory receipts...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with pagination parameters
        params = {
            "page": 1,
            "page_size": 10,
            "sort_by": "receipt_date",
            "sort_order": "desc"
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-receipts/", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total" in data:
                print(f"✅ Get inventory receipts test passed (Found {data['total']} receipts)")
                return True
            else:
                print(f"❌ Get inventory receipts test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get inventory receipts test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get inventory receipts test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get inventory receipts test failed: {str(e)}")
        return False

def test_get_receipt_by_id(receipt_id):
    """Test getting a receipt by ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not receipt_id:
        print("❌ Get receipt by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get receipt by ID: {receipt_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-receipts/{receipt_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "receipt_id" in data and data["receipt_id"] == receipt_id:
                print("✅ Get receipt by ID test passed")
                return True
            else:
                print(f"❌ Get receipt by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get receipt by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get receipt by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get receipt by ID test failed: {str(e)}")
        return False

def test_create_inventory_assembly():
    """Test creating an inventory assembly"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create inventory assembly test skipped: No access token or company ID available")
        return False, None
    
    # First, get two items for the assembly
    try:
        print("\n🔍 Getting items for inventory assembly...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        item_response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/items/", 
            headers=headers,
            params={"page": 1, "page_size": 2},
            timeout=TIMEOUT
        )
        
        if item_response.status_code != 200:
            print(f"❌ Failed to get items: Status code {item_response.status_code}")
            return False, None
        
        item_data = item_response.json()
        if not item_data.get("items") or len(item_data["items"]) < 2:
            print("❌ Not enough items found for assembly")
            return False, None
        
        assembly_item_id = item_data["items"][0]["item_id"]
        component_item_id = item_data["items"][1]["item_id"]
        print(f"Found assembly item ID: {assembly_item_id}, component item ID: {component_item_id}")
        
        # Now create the inventory assembly
        print("\n🔍 Testing create inventory assembly...")
        
        payload = {
            "assembly_item_id": assembly_item_id,
            "component_item_id": component_item_id,
            "quantity_needed": 2,
            "unit_cost": 15.00,
            "build_sequence": 1,
            "is_optional": False,
            "notes": "Test assembly via API"
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-assemblies/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "assembly_id" in data:
                assembly_id = data["assembly_id"]
                print(f"✅ Create inventory assembly test passed (ID: {assembly_id})")
                return True, assembly_id
            else:
                print(f"❌ Create inventory assembly test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create inventory assembly test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create inventory assembly test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create inventory assembly test failed: {str(e)}")
        return False, None

def test_get_inventory_assemblies():
    """Test getting inventory assemblies"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get inventory assemblies test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get inventory assemblies...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-assemblies/", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if isinstance(data, list):
                print(f"✅ Get inventory assemblies test passed (Found {len(data)} assemblies)")
                return True
            else:
                print(f"❌ Get inventory assemblies test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get inventory assemblies test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get inventory assemblies test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get inventory assemblies test failed: {str(e)}")
        return False

def test_update_inventory_assembly(assembly_id):
    """Test updating an inventory assembly"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not assembly_id:
        print("❌ Update inventory assembly test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing update inventory assembly: {assembly_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Updated assembly data
        payload = {
            "quantity_needed": 3,
            "unit_cost": 18.00,
            "notes": f"Updated assembly notes {datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        response = requests.put(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-assemblies/{assembly_id}", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "assembly_id" in data and data["assembly_id"] == assembly_id:
                print("✅ Update inventory assembly test passed")
                return True
            else:
                print(f"❌ Update inventory assembly test failed: Unexpected response")
                return False
        else:
            print(f"❌ Update inventory assembly test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Update inventory assembly test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Update inventory assembly test failed: {str(e)}")
        return False

def test_inventory_reorder_report():
    """Test generating inventory reorder report"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Inventory reorder report test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing inventory reorder report...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-reorder/report", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total_items" in data:
                print(f"✅ Inventory reorder report test passed (Found {data['total_items']} items)")
                return True
            else:
                print(f"❌ Inventory reorder report test failed: Unexpected response")
                return False
        else:
            print(f"❌ Inventory reorder report test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Inventory reorder report test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Inventory reorder report test failed: {str(e)}")
        return False

def test_auto_generate_purchase_orders():
    """Test auto-generating purchase orders"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Auto-generate purchase orders test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing auto-generate purchase orders...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-reorder/auto-generate-pos", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            print(f"✅ Auto-generate purchase orders test passed (Generated {len(data)} purchase orders)")
            return True
        else:
            print(f"❌ Auto-generate purchase orders test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Auto-generate purchase orders test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Auto-generate purchase orders test failed: {str(e)}")
        return False

def run_inventory_management_tests():
    """Run all Inventory Management Module API tests"""
    print("\n🔍 Starting QuickBooks Clone Inventory Management Module API tests...")
    print(f"🕒 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results
    results = {}
    
    # Login and get company access
    results["login_demo_user"] = test_login_demo_user()
    if results["login_demo_user"]:
        results["get_user_companies"] = test_get_user_companies()
        if COMPANY_ID:
            results["company_access"] = test_company_access()
        else:
            print("❌ No company ID available, skipping company-specific tests")
            return False
    else:
        print("❌ Login failed, skipping all other tests")
        return False
    
    # Test Inventory Overview
    print("\n📋 Testing Inventory Overview...")
    results["inventory_overview"] = test_inventory_overview()
    results["get_low_stock_items"] = test_get_low_stock_items()
    
    # Test Inventory Locations
    print("\n📋 Testing Inventory Locations...")
    location_result, location_id = test_create_inventory_location()
    results["create_inventory_location"] = location_result
    
    results["get_inventory_locations"] = test_get_inventory_locations()
    
    if location_id:
        results["update_inventory_location"] = test_update_inventory_location(location_id)
    
    # Test Inventory Adjustments
    print("\n📋 Testing Inventory Adjustments...")
    adjustment_result, adjustment_id = test_create_inventory_adjustment()
    results["create_inventory_adjustment"] = adjustment_result
    
    results["get_inventory_adjustments"] = test_get_inventory_adjustments()
    
    if adjustment_id:
        results["get_adjustment_by_id"] = test_get_adjustment_by_id(adjustment_id)
    
    # Test Purchase Orders
    print("\n📋 Testing Purchase Orders...")
    po_result, po_id = test_create_purchase_order()
    results["create_purchase_order"] = po_result
    
    results["get_purchase_orders"] = test_get_purchase_orders()
    
    if po_id:
        results["get_purchase_order_by_id"] = test_get_purchase_order_by_id(po_id)
        results["update_purchase_order"] = test_update_purchase_order(po_id)
    
    # Test Inventory Receipts
    print("\n📋 Testing Inventory Receipts...")
    receipt_result, receipt_id = test_create_inventory_receipt(po_id if po_result else None)
    results["create_inventory_receipt"] = receipt_result
    
    results["get_inventory_receipts"] = test_get_inventory_receipts()
    
    if receipt_id:
        results["get_receipt_by_id"] = test_get_receipt_by_id(receipt_id)
    
    # Test Inventory Assemblies
    print("\n📋 Testing Inventory Assemblies...")
    assembly_result, assembly_id = test_create_inventory_assembly()
    results["create_inventory_assembly"] = assembly_result
    
    results["get_inventory_assemblies"] = test_get_inventory_assemblies()
    
    if assembly_id:
        results["update_inventory_assembly"] = test_update_inventory_assembly(assembly_id)
    
    # Test Inventory Reorder
    print("\n📋 Testing Inventory Reorder...")
    results["inventory_reorder_report"] = test_inventory_reorder_report()
    results["auto_generate_purchase_orders"] = test_auto_generate_purchase_orders()
    
    # Print summary
    print("\n📊 Inventory Management Module Test Summary:")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Calculate overall success rate
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"\n🏆 Overall Success Rate: {success_rate:.2f}% ({success_count}/{total_count} tests passed)")
    
    return success_rate >= 80  # Consider test suite successful if at least 80% of tests pass

def test_inventory_overview():
    """Test getting inventory overview"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Inventory overview test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing inventory overview...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory/", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "total_items" in data and "total_value" in data:
                print("✅ Inventory overview test passed")
                return True
            else:
                print(f"❌ Inventory overview test failed: Unexpected response")
                return False
        else:
            print(f"❌ Inventory overview test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Inventory overview test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Inventory overview test failed: {str(e)}")
        return False

def test_get_item_inventory(item_id):
    """Test getting inventory for a specific item"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not item_id:
        print("❌ Get item inventory test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get item inventory for item ID: {item_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory/{item_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "item_id" in data and data["item_id"] == item_id:
                print("✅ Get item inventory test passed")
                return True
            else:
                print(f"❌ Get item inventory test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get item inventory test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get item inventory test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get item inventory test failed: {str(e)}")
        return False

def test_get_item_transactions(item_id):
    """Test getting transaction history for an item"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not item_id:
        print("❌ Get item transactions test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get item transactions for item ID: {item_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory/{item_id}/transactions", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total" in data:
                print("✅ Get item transactions test passed")
                return True
            else:
                print(f"❌ Get item transactions test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get item transactions test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get item transactions test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get item transactions test failed: {str(e)}")
        return False

def test_get_low_stock_items():
    """Test getting low stock items"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get low stock items test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get low stock items...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory/low-stock", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            print("✅ Get low stock items test passed")
            return True
        else:
            print(f"❌ Get low stock items test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get low stock items test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get low stock items test failed: {str(e)}")
        return False

def test_create_inventory_valuation():
    """Test creating an inventory valuation"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create inventory valuation test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing create inventory valuation...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Current date for valuation
        today = datetime.now().strftime("%Y-%m-%d")
        
        payload = {
            "valuation_date": today,
            "cost_method": "average_cost",
            "include_inactive_items": False,
            "notes": "Test valuation created via API"
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/inventory/valuation", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 201:
            if "valuation_id" in data:
                print("✅ Create inventory valuation test passed")
                return True
            else:
                print(f"❌ Create inventory valuation test failed: Unexpected response")
                return False
        else:
            print(f"❌ Create inventory valuation test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Create inventory valuation test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Create inventory valuation test failed: {str(e)}")
        return False

def test_create_inventory_adjustment():
    """Test creating an inventory adjustment"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create inventory adjustment test skipped: No access token or company ID available")
        return False, None
    
    # First, get an item to adjust
    try:
        print("\n🔍 Getting an item for inventory adjustment...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/items/", 
            headers=headers,
            params={"page": 1, "page_size": 1},
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get items: Status code {response.status_code}")
            return False, None
        
        data = response.json()
        if not data.get("items") or len(data["items"]) == 0:
            print("❌ No items found to adjust")
            return False, None
        
        item_id = data["items"][0]["item_id"]
    except Exception as e:
        print(f"❌ Failed to get items: {str(e)}")
        return False, None
    
    # Now create the adjustment
    try:
        print(f"\n🔍 Testing create inventory adjustment for item ID: {item_id}...")
        
        # Current date for adjustment
        today = datetime.now().strftime("%Y-%m-%d")
        
        payload = {
            "item_id": item_id,
            "adjustment_date": today,
            "adjustment_type": "quantity",
            "quantity_before": 0,
            "quantity_after": 10,
            "quantity_adjustment": 10,
            "value_before": 0,
            "value_after": 100,
            "value_adjustment": 100,
            "unit_cost": 10,
            "reason_code": "INITIAL",
            "memo": "Initial inventory setup"
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-adjustments/", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "adjustment_id" in data:
                adjustment_id = data["adjustment_id"]
                print(f"✅ Create inventory adjustment test passed (ID: {adjustment_id})")
                return True, adjustment_id
            else:
                print(f"❌ Create inventory adjustment test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create inventory adjustment test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create inventory adjustment test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create inventory adjustment test failed: {str(e)}")
        return False, None

def test_get_inventory_adjustments():
    """Test getting inventory adjustments"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get inventory adjustments test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get inventory adjustments...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        params = {
            "page": 1,
            "page_size": 10,
            "sort_by": "adjustment_date",
            "sort_order": "desc"
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-adjustments/", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "items" in data and "total" in data:
                print(f"✅ Get inventory adjustments test passed (Found {data['total']} adjustments)")
                return True
            else:
                print(f"❌ Get inventory adjustments test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get inventory adjustments test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get inventory adjustments test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get inventory adjustments test failed: {str(e)}")
        return False

def test_get_adjustment_by_id(adjustment_id):
    """Test getting an adjustment by ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not adjustment_id:
        print("❌ Get adjustment by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get adjustment by ID: {adjustment_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/inventory-adjustments/{adjustment_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "adjustment_id" in data and data["adjustment_id"] == adjustment_id:
                print("✅ Get adjustment by ID test passed")
                return True
            else:
                print(f"❌ Get adjustment by ID test failed: Unexpected response")
                return False
        elif response.status_code == 404:
            print("ℹ️ Adjustment not found (API returns 404)")
            return False
        else:
            print(f"❌ Get adjustment by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get adjustment by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get adjustment by ID test failed: {str(e)}")
        return False

def test_create_purchase_order():
    """Test creating a purchase order"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create purchase order test skipped: No access token or company ID available")
        return False, None
    
    # First, get a vendor
    try:
        print("\n🔍 Getting a vendor for purchase order...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/vendors/", 
            headers=headers,
            params={"page": 1, "page_size": 1},
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get vendors: Status code {response.status_code}")
            return False, None
        
        data = response.json()
        if not data.get("items") or len(data["items"]) == 0:
            print("❌ No vendors found for purchase order")
            return False, None
        
        vendor_id = data["items"][0]["vendor_id"]
    except Exception as e:
        print(f"❌ Failed to get vendors: {str(e)}")
        return False, None
    
    # Next, get an item
    try:
        print("\n🔍 Getting an item for purchase order...")
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/items/", 
            headers=headers,
            params={"page": 1, "page_size": 1},
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get items: Status code {response.status_code}")
            return False, None
        
        data = response.json()
        if not data.get("items") or len(data["items"]) == 0:
            print("❌ No items found for purchase order")
            return False, None
        
        item_id = data["items"][0]["item_id"]
    except Exception as e:
        print(f"❌ Failed to get items: {str(e)}")
        return False, None
    
    # Now create the purchase order
    try:
        print(f"\n🔍 Testing create purchase order for vendor ID: {vendor_id}...")
        
        # Current date for PO
        today = datetime.now().strftime("%Y-%m-%d")
        expected_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Generate a unique PO number
        po_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        payload = {
            "po_number": po_number,
            "vendor_id": vendor_id,
            "po_date": today,
            "expected_date": expected_date,
            "status": "open",
            "memo": "Test purchase order created via API",
            "po_lines": [
                {
                    "line_number": 1,
                    "item_id": item_id,
                    "description": "Test item",
                    "quantity_ordered": 10,
                    "unit_cost": 25.50,
                    "line_total": 255.00
                }
            ]
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/purchase-orders/", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "purchase_order_id" in data:
                po_id = data["purchase_order_id"]
                print(f"✅ Create purchase order test passed (ID: {po_id})")
                return True, po_id
            else:
                print(f"❌ Create purchase order test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create purchase order test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create purchase order test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create purchase order test failed: {str(e)}")
        return False, None

def run_inventory_management_tests():
    """Run all Inventory Management Module API tests"""
    print("\n🔍 Starting QuickBooks Clone Inventory Management Module API tests...")
    print(f"🕒 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results
    results = {}
    
    # Login and get company access
    results["login_demo_user"] = test_login_demo_user()
    if results["login_demo_user"]:
        results["get_user_companies"] = test_get_user_companies()
        if COMPANY_ID:
            results["company_access"] = test_company_access()
        else:
            print("❌ No company ID available, skipping company-specific tests")
            return False
    else:
        print("❌ Login failed, skipping all other tests")
        return False
    
    # Test General Inventory API
    print("\n📋 Testing General Inventory API...")
    results["inventory_overview"] = test_inventory_overview()
    
    # Get an item for testing
    try:
        print("\n🔍 Getting an item for inventory tests...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/items/", 
            headers=headers,
            params={"page": 1, "page_size": 1},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("items") and len(data["items"]) > 0:
                item_id = data["items"][0]["item_id"]
                print(f"Found item ID: {item_id}")
                
                results["get_item_inventory"] = test_get_item_inventory(item_id)
                results["get_item_transactions"] = test_get_item_transactions(item_id)
            else:
                print("❌ No items found for testing")
        else:
            print(f"❌ Failed to get items: Status code {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to get items: {str(e)}")
    
    results["get_low_stock_items"] = test_get_low_stock_items()
    results["create_inventory_valuation"] = test_create_inventory_valuation()
    
    # Test Inventory Adjustments API
    print("\n📋 Testing Inventory Adjustments API...")
    adjustment_result, adjustment_id = test_create_inventory_adjustment()
    results["create_inventory_adjustment"] = adjustment_result
    
    results["get_inventory_adjustments"] = test_get_inventory_adjustments()
    
    if adjustment_id:
        results["get_adjustment_by_id"] = test_get_adjustment_by_id(adjustment_id)
    
    # Test Purchase Orders API
    print("\n📋 Testing Purchase Orders API...")
    po_result, po_id = test_create_purchase_order()
    results["create_purchase_order"] = po_result
    
    # Print summary
    print("\n📊 Inventory Management Module API Test Summary:")
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    print(f"✅ {success_count}/{total_count} tests passed ({success_count/total_count*100:.1f}%)")
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    return success_count == total_count

def test_create_invoice():
    """Test creating an invoice"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create invoice test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create invoice...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique reference number
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # First, create a customer if needed
        customer_result, customer_id = test_create_customer()
        if not customer_result or not customer_id:
            print("❌ Create invoice test skipped: Failed to create test customer")
            return False, None
        
        # Create an invoice with line items
        payload = {
            "transaction_date": datetime.now().date().isoformat(),
            "due_date": (datetime.now().date() + timedelta(days=30)).isoformat(),
            "customer_id": customer_id,
            "reference_number": f"REF-INV-{timestamp}",
            "memo": "Test invoice created via API",
            "lines": [
                {
                    "line_number": 1,
                    "line_type": "item",
                    "description": "Test Product 1",
                    "quantity": 2,
                    "unit_price": 100.00,
                    "discount_amount": 10.00,
                    "tax_amount": 15.00
                },
                {
                    "line_number": 2,
                    "line_type": "item",
                    "description": "Test Service 1",
                    "quantity": 5,
                    "unit_price": 50.00,
                    "discount_amount": 5.00,
                    "tax_amount": 20.00
                }
            ]
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/invoices/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "transaction_id" in data:
                invoice_id = data["transaction_id"]
                
                # Verify the calculated totals
                subtotal = data.get("subtotal")
                tax_amount = data.get("tax_amount")
                total_amount = data.get("total_amount")
                
                print(f"Invoice created with ID: {invoice_id}")
                print(f"Subtotal: {subtotal}")
                print(f"Tax Amount: {tax_amount}")
                print(f"Total Amount: {total_amount}")
                
                # Expected calculations:
                # Line 1: (2 * 100) - 10 + 15 = 205
                # Line 2: (5 * 50) - 5 + 20 = 265
                # Subtotal: (2 * 100) + (5 * 50) - 10 - 5 = 435
                # Tax Amount: 15 + 20 = 35
                # Total Amount: 435 + 35 = 470
                
                expected_subtotal = 435.0
                expected_tax = 35.0
                expected_total = 470.0
                
                if (abs(float(subtotal) - expected_subtotal) < 0.01 and 
                    abs(float(tax_amount) - expected_tax) < 0.01 and 
                    abs(float(total_amount) - expected_total) < 0.01):
                    print("✅ Invoice calculations are correct")
                else:
                    print(f"❌ Invoice calculations are incorrect. Expected: Subtotal={expected_subtotal}, Tax={expected_tax}, Total={expected_total}")
                
                print(f"✅ Create invoice test passed (ID: {invoice_id})")
                return True, invoice_id
            else:
                print(f"❌ Create invoice test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create invoice test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create invoice test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create invoice test failed: {str(e)}")
        return False, None

def test_create_bill():
    """Test creating a bill"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create bill test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create bill...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique reference number
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # First, create a vendor if needed
        vendor_result, vendor_id = test_create_vendor()
        if not vendor_result or not vendor_id:
            print("❌ Create bill test skipped: Failed to create test vendor")
            return False, None
        
        # Create a bill with line items
        payload = {
            "transaction_date": datetime.now().date().isoformat(),
            "due_date": (datetime.now().date() + timedelta(days=30)).isoformat(),
            "vendor_id": vendor_id,
            "reference_number": f"REF-BILL-{timestamp}",
            "memo": "Test bill created via API",
            "lines": [
                {
                    "line_number": 1,
                    "line_type": "item",
                    "description": "Office Supplies",
                    "quantity": 3,
                    "unit_price": 75.00,
                    "discount_amount": 15.00,
                    "tax_amount": 12.00
                },
                {
                    "line_number": 2,
                    "line_type": "item",
                    "description": "Consulting Services",
                    "quantity": 10,
                    "unit_price": 120.00,
                    "discount_amount": 50.00,
                    "tax_amount": 80.00
                }
            ]
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/bills/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "transaction_id" in data:
                bill_id = data["transaction_id"]
                
                # Verify the calculated totals
                subtotal = data.get("subtotal")
                tax_amount = data.get("tax_amount")
                total_amount = data.get("total_amount")
                
                print(f"Bill created with ID: {bill_id}")
                print(f"Subtotal: {subtotal}")
                print(f"Tax Amount: {tax_amount}")
                print(f"Total Amount: {total_amount}")
                
                # Expected calculations:
                # Line 1: (3 * 75) - 15 + 12 = 222
                # Line 2: (10 * 120) - 50 + 80 = 1230
                # Subtotal: (3 * 75) + (10 * 120) - 15 - 50 = 1160
                # Tax Amount: 12 + 80 = 92
                # Total Amount: 1160 + 92 = 1252
                
                expected_subtotal = 1160.0
                expected_tax = 92.0
                expected_total = 1252.0
                
                if (abs(float(subtotal) - expected_subtotal) < 0.01 and 
                    abs(float(tax_amount) - expected_tax) < 0.01 and 
                    abs(float(total_amount) - expected_total) < 0.01):
                    print("✅ Bill calculations are correct")
                else:
                    print(f"❌ Bill calculations are incorrect. Expected: Subtotal={expected_subtotal}, Tax={expected_tax}, Total={expected_total}")
                
                print(f"✅ Create bill test passed (ID: {bill_id})")
                return True, bill_id
            else:
                print(f"❌ Create bill test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create bill test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create bill test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create bill test failed: {str(e)}")
        return False, None

def test_create_payment():
    """Test creating a payment"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create payment test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create payment...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique reference number
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # First, create a customer and an invoice
        invoice_result, invoice_id = test_create_invoice()
        if not invoice_result or not invoice_id:
            print("❌ Create payment test skipped: Failed to create test invoice")
            return False, None
        
        # Create an account for deposit
        account_result, account_id = test_create_account()
        if not account_result or not account_id:
            print("❌ Create payment test skipped: Failed to create test account")
            return False, None
        
        # Create a payment
        payload = {
            "payment_date": datetime.now().date().isoformat(),
            "payment_type": "check",
            "payment_method": "Check #12345",
            "reference_number": f"REF-PMT-{timestamp}",
            "customer_id": invoice_id,  # Using invoice_id as customer_id for simplicity
            "amount_received": 250.00,
            "deposit_to_account_id": account_id,
            "memo": "Test payment created via API",
            "applications": [
                {
                    "transaction_id": invoice_id,
                    "amount_applied": 250.00,
                    "discount_taken": 0.00
                }
            ]
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/payments/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "payment_id" in data:
                payment_id = data["payment_id"]
                print(f"✅ Create payment test passed (ID: {payment_id})")
                return True, payment_id
            else:
                print(f"❌ Create payment test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create payment test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create payment test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create payment test failed: {str(e)}")
        return False, None

def test_create_transaction():
    """Test creating a general transaction"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create transaction test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create general transaction...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique reference number
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create a general transaction
        payload = {
            "transaction_type": "journal_entry",
            "transaction_date": datetime.now().date().isoformat(),
            "reference_number": f"REF-JE-{timestamp}",
            "memo": "Test journal entry created via API",
            "lines": [
                {
                    "line_number": 1,
                    "line_type": "account",
                    "description": "Debit Entry",
                    "quantity": 1,
                    "unit_price": 500.00,
                    "discount_amount": 0.00,
                    "tax_amount": 0.00
                },
                {
                    "line_number": 2,
                    "line_type": "account",
                    "description": "Credit Entry",
                    "quantity": 1,
                    "unit_price": 500.00,
                    "discount_amount": 0.00,
                    "tax_amount": 0.00
                }
            ]
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/transactions/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "transaction_id" in data:
                transaction_id = data["transaction_id"]
                
                # Verify the calculated totals
                subtotal = data.get("subtotal")
                tax_amount = data.get("tax_amount")
                total_amount = data.get("total_amount")
                
                print(f"Transaction created with ID: {transaction_id}")
                print(f"Subtotal: {subtotal}")
                print(f"Tax Amount: {tax_amount}")
                print(f"Total Amount: {total_amount}")
                
                # Expected calculations:
                # Line 1: (1 * 500) - 0 + 0 = 500
                # Line 2: (1 * 500) - 0 + 0 = 500
                # Subtotal: (1 * 500) + (1 * 500) - 0 - 0 = 1000
                # Tax Amount: 0 + 0 = 0
                # Total Amount: 1000 + 0 = 1000
                
                expected_subtotal = 1000.0
                expected_tax = 0.0
                expected_total = 1000.0
                
                if (abs(float(subtotal) - expected_subtotal) < 0.01 and 
                    abs(float(tax_amount) - expected_tax) < 0.01 and 
                    abs(float(total_amount) - expected_total) < 0.01):
                    print("✅ Transaction calculations are correct")
                else:
                    print(f"❌ Transaction calculations are incorrect. Expected: Subtotal={expected_subtotal}, Tax={expected_tax}, Total={expected_total}")
                
                print(f"✅ Create transaction test passed (ID: {transaction_id})")
                return True, transaction_id
            else:
                print(f"❌ Create transaction test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create transaction test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create transaction test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create transaction test failed: {str(e)}")
        return False, None

def test_create_sales_receipt():
    """Test creating a sales receipt"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create sales receipt test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create sales receipt...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique reference number
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # First, create a customer if needed
        customer_result, customer_id = test_create_customer()
        if not customer_result or not customer_id:
            print("❌ Create sales receipt test skipped: Failed to create test customer")
            return False, None
        
        # Create a sales receipt with line items
        payload = {
            "transaction_type": "sales_receipt",
            "transaction_date": datetime.now().date().isoformat(),
            "customer_id": customer_id,
            "reference_number": f"REF-SR-{timestamp}",
            "memo": "Test sales receipt created via API",
            "lines": [
                {
                    "line_number": 1,
                    "line_type": "item",
                    "description": "Product Sale 1",
                    "quantity": 2,
                    "unit_price": 75.00,
                    "discount_amount": 5.00,
                    "tax_amount": 10.00
                },
                {
                    "line_number": 2,
                    "line_type": "item",
                    "description": "Product Sale 2",
                    "quantity": 1,
                    "unit_price": 150.00,
                    "discount_amount": 0.00,
                    "tax_amount": 15.00
                }
            ]
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/transactions/", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "transaction_id" in data:
                receipt_id = data["transaction_id"]
                
                # Verify the calculated totals
                subtotal = data.get("subtotal")
                tax_amount = data.get("tax_amount")
                total_amount = data.get("total_amount")
                
                print(f"Sales Receipt created with ID: {receipt_id}")
                print(f"Subtotal: {subtotal}")
                print(f"Tax Amount: {tax_amount}")
                print(f"Total Amount: {total_amount}")
                
                # Expected calculations:
                # Line 1: (2 * 75) - 5 + 10 = 155
                # Line 2: (1 * 150) - 0 + 15 = 165
                # Subtotal: (2 * 75) + (1 * 150) - 5 - 0 = 295
                # Tax Amount: 10 + 15 = 25
                # Total Amount: 295 + 25 = 320
                
                expected_subtotal = 295.0
                expected_tax = 25.0
                expected_total = 320.0
                
                if (abs(float(subtotal) - expected_subtotal) < 0.01 and 
                    abs(float(tax_amount) - expected_tax) < 0.01 and 
                    abs(float(total_amount) - expected_total) < 0.01):
                    print("✅ Sales Receipt calculations are correct")
                else:
                    print(f"❌ Sales Receipt calculations are incorrect. Expected: Subtotal={expected_subtotal}, Tax={expected_tax}, Total={expected_total}")
                
                print(f"✅ Create sales receipt test passed (ID: {receipt_id})")
                return True, receipt_id
            else:
                print(f"❌ Create sales receipt test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create sales receipt test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create sales receipt test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create sales receipt test failed: {str(e)}")
        return False, None

def run_transaction_engine_tests():
    """Run all Transaction Engine Module API tests"""
    print("\n🔍 Starting QuickBooks Clone Transaction Engine Module API tests...")
    print(f"🕒 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results
    results = {}
    
    # Login and get company access
    results["login_demo_user"] = test_login_demo_user()
    if results["login_demo_user"]:
        results["get_user_companies"] = test_get_user_companies()
        if COMPANY_ID:
            results["company_access"] = test_company_access()
        else:
            print("❌ No company ID available, skipping transaction tests")
            return False
    else:
        print("❌ Login failed, skipping all transaction tests")
        return False
    
    # Test Transaction Engine APIs
    print("\n📋 Testing Transaction Engine APIs...")
    
    # Test Invoice Creation
    invoice_result, invoice_id = test_create_invoice()
    results["create_invoice"] = invoice_result
    
    # Test Bill Creation
    bill_result, bill_id = test_create_bill()
    results["create_bill"] = bill_result
    
    # Test Payment Creation
    payment_result, payment_id = test_create_payment()
    results["create_payment"] = payment_result
    
    # Test General Transaction Creation
    transaction_result, transaction_id = test_create_transaction()
    results["create_transaction"] = transaction_result
    
    # Test Sales Receipt Creation
    receipt_result, receipt_id = test_create_sales_receipt()
    results["create_sales_receipt"] = receipt_result
    
    # Print summary
    print("\n📊 Transaction Engine Module Test Summary:")
    for test_name, result in results.items():
        status = "✅ Passed" if result else "❌ Failed"
        print(f"{test_name}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All Transaction Engine Module tests passed!")
    else:
        print("\n❌ Some Transaction Engine Module tests failed.")
    
    return all_passed

# ===== BANKING INTEGRATION TESTS =====

def test_create_bank_connection():
    """Test creating a bank connection"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Create bank connection test skipped: No access token or company ID available")
        return False, None
    
    try:
        print("\n🔍 Testing create bank connection...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Generate a unique connection name to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        payload = {
            "connection_name": f"Test Bank Connection {timestamp}",
            "institution_id": "inst_001",
            "account_type": "checking",
            "account_number": f"12345678{timestamp}",
            "routing_number": "111000025",
            "connection_status": "active",
            "last_sync_date": datetime.now().isoformat(),
            "balance": 5000.00,
            "currency": "USD"
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/bank-connections", 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False, None
        
        if response.status_code == 201:
            if "connection_id" in data and data.get("connection_name") == payload["connection_name"]:
                connection_id = data["connection_id"]
                print(f"✅ Create bank connection test passed (ID: {connection_id})")
                return True, connection_id
            else:
                print(f"❌ Create bank connection test failed: Unexpected response")
                return False, None
        else:
            print(f"❌ Create bank connection test failed: Status code {response.status_code}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Create bank connection test failed: Request timed out after {TIMEOUT} seconds")
        return False, None
    except Exception as e:
        print(f"❌ Create bank connection test failed: {str(e)}")
        return False, None

def test_get_bank_connections():
    """Test getting bank connections"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get bank connections test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get bank connections...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with pagination parameters
        params = {
            "skip": 0,
            "limit": 10,
            "is_active": True
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/bank-connections", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "connections" in data and "total" in data and "page" in data:
                print(f"✅ Get bank connections test passed (Found {data['total']} connections)")
                return True
            else:
                print(f"❌ Get bank connections test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get bank connections test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get bank connections test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get bank connections test failed: {str(e)}")
        return False

def test_get_bank_connection_by_id(connection_id):
    """Test getting a bank connection by ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not connection_id:
        print("❌ Get bank connection by ID test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get bank connection by ID: {connection_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/bank-connections/{connection_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "connection_id" in data and data["connection_id"] == connection_id:
                print("✅ Get bank connection by ID test passed")
                return True
            else:
                print(f"❌ Get bank connection by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get bank connection by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get bank connection by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get bank connection by ID test failed: {str(e)}")
        return False

def test_update_bank_connection(connection_id):
    """Test updating a bank connection"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not connection_id:
        print("❌ Update bank connection test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing update bank connection: {connection_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Updated connection data
        payload = {
            "connection_name": f"Updated Bank Connection {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "balance": 7500.00,
            "connection_status": "active"
        }
        
        response = requests.put(
            f"{API_URL}/companies/{COMPANY_ID}/bank-connections/{connection_id}", 
            headers=headers, 
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "connection_id" in data and data["connection_id"] == connection_id:
                print("✅ Update bank connection test passed")
                return True
            else:
                print(f"❌ Update bank connection test failed: Unexpected response")
                return False
        else:
            print(f"❌ Update bank connection test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Update bank connection test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Update bank connection test failed: {str(e)}")
        return False

def test_sync_bank_connection(connection_id):
    """Test syncing a bank connection"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not connection_id:
        print("❌ Sync bank connection test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing sync bank connection: {connection_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/bank-connections/{connection_id}/sync", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "message" in data and "sync" in data["message"].lower():
                print("✅ Sync bank connection test passed")
                return True
            else:
                print(f"❌ Sync bank connection test failed: Unexpected response")
                return False
        else:
            print(f"❌ Sync bank connection test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Sync bank connection test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Sync bank connection test failed: {str(e)}")
        return False

def test_get_bank_transactions():
    """Test getting bank transactions"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Get bank transactions test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing get bank transactions...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with filtering parameters
        params = {
            "skip": 0,
            "limit": 20,
            "start_date": (datetime.now() - timedelta(days=30)).date().isoformat(),
            "end_date": datetime.now().date().isoformat(),
            "status": "unmatched"
        }
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/bank-transactions", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "transactions" in data and "total" in data and "page" in data:
                print(f"✅ Get bank transactions test passed (Found {data['total']} transactions)")
                return True
            else:
                print(f"❌ Get bank transactions test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get bank transactions test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get bank transactions test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get bank transactions test failed: {str(e)}")
        return False

def test_get_bank_transactions_by_connection(connection_id):
    """Test getting bank transactions by connection ID"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not connection_id:
        print("❌ Get bank transactions by connection test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing get bank transactions by connection: {connection_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(
            f"{API_URL}/companies/{COMPANY_ID}/bank-transactions/{connection_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if isinstance(data, list):
                print(f"✅ Get bank transactions by connection test passed (Found {len(data)} transactions)")
                return True
            else:
                print(f"❌ Get bank transactions by connection test failed: Expected list response")
                return False
        else:
            print(f"❌ Get bank transactions by connection test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get bank transactions by connection test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get bank transactions by connection test failed: {str(e)}")
        return False

def test_search_institutions():
    """Test searching bank institutions"""
    global ACCESS_TOKEN
    
    if not ACCESS_TOKEN:
        print("❌ Search institutions test skipped: No access token available")
        return False
    
    try:
        print("\n🔍 Testing search bank institutions...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Test with search parameters
        params = {
            "name_contains": "Bank",
            "skip": 0,
            "limit": 10,
            "supports_ofx": True
        }
        
        response = requests.get(
            f"{API_URL}/banking/institutions/search", 
            headers=headers, 
            params=params,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "institutions" in data and "total" in data:
                print(f"✅ Search institutions test passed (Found {data['total']} institutions)")
                return True
            else:
                print(f"❌ Search institutions test failed: Unexpected response")
                return False
        else:
            print(f"❌ Search institutions test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Search institutions test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Search institutions test failed: {str(e)}")
        return False

def test_get_institution_by_id():
    """Test getting a bank institution by ID"""
    global ACCESS_TOKEN
    
    if not ACCESS_TOKEN:
        print("❌ Get institution by ID test skipped: No access token available")
        return False
    
    try:
        print("\n🔍 Testing get bank institution by ID...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Use a known institution ID from the sample data
        institution_id = "inst_001"
        
        response = requests.get(
            f"{API_URL}/banking/institutions/{institution_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "institution_id" in data and data["institution_id"] == institution_id:
                print("✅ Get institution by ID test passed")
                return True
            else:
                print(f"❌ Get institution by ID test failed: Unexpected response")
                return False
        else:
            print(f"❌ Get institution by ID test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Get institution by ID test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Get institution by ID test failed: {str(e)}")
        return False

def test_upload_bank_statement():
    """Test uploading a bank statement file"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID:
        print("❌ Upload bank statement test skipped: No access token or company ID available")
        return False
    
    try:
        print("\n🔍 Testing upload bank statement...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        # Create a simple CSV content for testing
        csv_content = """Date,Description,Amount,Type
2023-07-01,Initial Deposit,1000.00,credit
2023-07-02,Coffee Shop,-5.50,debit
2023-07-03,Salary Deposit,2500.00,credit
2023-07-04,Grocery Store,-120.75,debit"""
        
        # Create a test file
        files = {
            'file': ('test_statement.csv', csv_content, 'text/csv')
        }
        
        data = {
            'file_type': 'csv',
            'connection_id': 'test_connection_123'
        }
        
        response = requests.post(
            f"{API_URL}/companies/{COMPANY_ID}/bank-statements/upload", 
            headers=headers,
            files=files,
            data=data,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {pretty_print_json(response_data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "upload_id" in response_data and "status" in response_data:
                print("✅ Upload bank statement test passed")
                return True
            else:
                print(f"❌ Upload bank statement test failed: Unexpected response")
                return False
        else:
            print(f"❌ Upload bank statement test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Upload bank statement test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Upload bank statement test failed: {str(e)}")
        return False

def test_delete_bank_connection(connection_id):
    """Test deleting a bank connection"""
    global ACCESS_TOKEN, COMPANY_ID
    
    if not ACCESS_TOKEN or not COMPANY_ID or not connection_id:
        print("❌ Delete bank connection test skipped: Missing required data")
        return False
    
    try:
        print(f"\n🔍 Testing delete bank connection: {connection_id}...")
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.delete(
            f"{API_URL}/companies/{COMPANY_ID}/bank-connections/{connection_id}", 
            headers=headers, 
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {pretty_print_json(data)}")
        except:
            print(f"Response: {response.text}")
            return False
        
        if response.status_code == 200:
            if "message" in data and "deleted" in data["message"].lower():
                print("✅ Delete bank connection test passed")
                return True
            else:
                print(f"❌ Delete bank connection test failed: Unexpected response")
                return False
        else:
            print(f"❌ Delete bank connection test failed: Status code {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Delete bank connection test failed: Request timed out after {TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"❌ Delete bank connection test failed: {str(e)}")
        return False


def run_banking_integration_tests():
    """Run all Banking Integration Module API tests"""
    print("\n🔍 Starting QuickBooks Clone Banking Integration Module API tests...")
    print(f"🕒 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results
    results = {}
    
    # Login and get company access
    results["login_demo_user"] = test_login_demo_user()
    if results["login_demo_user"]:
        results["get_user_companies"] = test_get_user_companies()
        if COMPANY_ID:
            results["company_access"] = test_company_access()
        else:
            print("❌ No company ID available, skipping banking tests")
            return False
    else:
        print("❌ Login failed, skipping all banking tests")
        return False
    
    # Test Banking Integration APIs
    print("\n📋 Testing Banking Integration APIs...")
    
    # Test Bank Connection Management
    print("\n🏦 Testing Bank Connection Management...")
    connection_result, connection_id = test_create_bank_connection()
    results["create_bank_connection"] = connection_result
    
    results["get_bank_connections"] = test_get_bank_connections()
    
    if connection_id:
        results["get_bank_connection_by_id"] = test_get_bank_connection_by_id(connection_id)
        results["update_bank_connection"] = test_update_bank_connection(connection_id)
        results["sync_bank_connection"] = test_sync_bank_connection(connection_id)
        results["get_bank_transactions_by_connection"] = test_get_bank_transactions_by_connection(connection_id)
    
    # Test Bank Transaction Management
    print("\n💳 Testing Bank Transaction Management...")
    results["get_bank_transactions"] = test_get_bank_transactions()
    
    # Test Institution Search
    print("\n🏛️ Testing Institution Search...")
    results["search_institutions"] = test_search_institutions()
    results["get_institution_by_id"] = test_get_institution_by_id()
    
    # Test File Upload
    print("\n📄 Testing File Upload...")
    results["upload_bank_statement"] = test_upload_bank_statement()
    
    # Clean up - delete the test connection
    if connection_id:
        results["delete_bank_connection"] = test_delete_bank_connection(connection_id)
    
    # Print summary
    print("\n📊 Banking Integration Module Test Summary:")
    for test_name, result in results.items():
        status = "✅ Passed" if result else "❌ Failed"
        print(f"{test_name}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All Banking Integration Module tests passed!")
    else:
        print("\n❌ Some Banking Integration Module tests failed.")
    
    return all_passed
