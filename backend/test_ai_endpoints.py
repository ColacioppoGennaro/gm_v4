#!/usr/bin/env python3
"""
Test AI endpoints with sample requests
"""
import requests
import json
import os

# Backend URL
BASE_URL = "https://gruppogea.net/gm_v4/api"

# You need a valid JWT token (get it by calling /api/auth/login first)
# For testing, use this placeholder
TEST_TOKEN = "your_jwt_token_here"

def test_ai_chat():
    """Test AI chat endpoint"""
    print("\n=== Testing AI Chat Endpoint ===")
    
    url = f"{BASE_URL}/ai/chat"
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {"role": "ai", "content": "Ciao! Come posso aiutarti?"},
            {"role": "user", "content": "Devo pagare la bolletta Enel di 150 euro entro il 30 ottobre"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")

def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    
    url = f"{BASE_URL}/health"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_document_analysis():
    """Test document analysis endpoint"""
    print("\n=== Testing Document Analysis ===")
    print("NOTE: This requires a sample image/PDF file to test")
    print("To test manually:")
    print(f"curl -X POST {BASE_URL}/ai/analyze-document \\")
    print(f"  -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print(f"  -F 'file=@/path/to/document.pdf'")

if __name__ == "__main__":
    print("SmartLife Organizer - AI Endpoints Test")
    print("=" * 50)
    
    # Check if running locally or against production
    if "localhost" in BASE_URL:
        print("⚠️  Testing against LOCAL backend")
    else:
        print("🌐 Testing against PRODUCTION backend")
    
    test_health_check()
    
    print("\n" + "=" * 50)
    print("To test AI endpoints, you need a valid JWT token:")
    print("1. Register/Login via /api/auth/login")
    print("2. Copy the 'access_token' from response")
    print("3. Set TEST_TOKEN variable in this script")
    print("4. Run: python test_ai_endpoints.py")
    print("=" * 50)
    
    # Uncomment when you have a valid token:
    # test_ai_chat()
    # test_document_analysis()
