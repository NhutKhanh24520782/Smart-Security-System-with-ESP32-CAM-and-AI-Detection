#!/usr/bin/env python3
"""
Test script to check backend endpoints and debug info
"""
import requests
import json
import time
import sys

def test_endpoints():
    base_url = "http://127.0.0.1:5002"
    
    endpoints = [
        ("/", "GET", "Root endpoint"),
        ("/health", "GET", "Health check"),
        ("/status", "GET", "Backend status + MQTT + ESP32 devices"),
    ]
    
    print("\n" + "="*60)
    print("🧪 Backend Endpoints Test")
    print("="*60 + "\n")
    
    for path, method, description in endpoints:
        try:
            url = f"{base_url}{path}"
            print(f"📍 Testing {method} {path}")
            print(f"   Description: {description}")
            
            if method == "GET":
                response = requests.get(url, timeout=3)
            
            print(f"   Status: {response.status_code}")
            
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=4)}")
            except:
                print(f"   Response: {response.text[:200]}")
            
            print()
            
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection refused - Backend might not be running")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)

if __name__ == "__main__":
    print("⏳ Waiting 2 seconds for backend to be ready...")
    time.sleep(2)
    test_endpoints()
