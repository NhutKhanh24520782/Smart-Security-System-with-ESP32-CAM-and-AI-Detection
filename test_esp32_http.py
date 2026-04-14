#!/usr/bin/env python3
"""
Quick HTTP test for ESP32 camera endpoints
Bypass motion detection and MQTT to test camera directly
"""

import requests
import sys
from datetime import datetime

def test_esp32_http(ip, port=80):
    """Test ESP32 HTTP endpoints"""
    base_url = f"http://{ip}:{port}"
    
    print(f"\n{'='*60}")
    print(f"Testing ESP32-CAM at {base_url}")
    print(f"{'='*60}")
    
    # Test 1: Health check
    print("\n1️⃣  Testing /health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        if response.status_code == 200:
            print("   ✅ Health check OK")
        else:
            print("   ⚠️  Unexpected status code")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 2: Test endpoint (manual capture test)
    print("\n2️⃣  Testing /test endpoint...")
    try:
        response = requests.get(f"{base_url}/test", timeout=3)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            image_size = len(response.content)
            print(f"   ✅ Image captured: {image_size} bytes")
            
            # Save test image
            filename = f"test_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"   💾 Saved to: {filename}")
            return True
        else:
            print(f"   ❌ HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout - camera may be stuck")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection error: {e}")
        print(f"   Check if ESP32 is online at {ip}")
        return False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 3: Capture endpoint
    print("\n3️⃣  Testing /capture endpoint...")
    try:
        response = requests.get(f"{base_url}/capture", timeout=3)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            image_size = len(response.content)
            print(f"   ✅ Image captured: {image_size} bytes")
            
            # Save captured image
            filename = f"capture_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"   💾 Saved to: {filename}")
            return True
        else:
            print(f"   ❌ HTTP {response.status_code}")
            print(f"   Response: {response.text}")
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout - camera not responding")
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection error: {e}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print(f"\n{'='*60}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_esp32.py <ESP32_IP> [port]")
        print("Example: python3 test_esp32.py 10.87.175.144")
        print("Example: python3 test_esp32.py 10.87.175.144 80")
        sys.exit(1)
    
    ip = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    
    success = test_esp32_http(ip, port)
    
    if success:
        print("\n✅ Camera is working! You can proceed to motion detection testing.")
        sys.exit(0)
    else:
        print("\n❌ Camera test failed. Check DEBUG_GUIDE.md for troubleshooting.")
        sys.exit(1)
