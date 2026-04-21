"""
Quick Start Guide for Face Detection & Recognition System
Ready-to-use patterns for common scenarios
"""

# ==================== QUICK START 1: Basic Detection ====================

def quick_start_detection():
    """Simplest way to detect and recognize faces"""
    
    from ai.detect import detect_and_recognize_faces
    
    # Read image from file
    with open('image.jpg', 'rb') as f:
        image_bytes = f.read()
    
    # Detect faces
    result = detect_and_recognize_faces(image_bytes)
    
    # Check results
    if result['human_detected']:
        print(f"Found {len(result['faces'])} face(s)")
        
        for face in result['faces']:
            if face['status'] == 'KNOWN':
                print(f"  ✅ {face['name']}: {face['confidence']:.1f}%")
            else:
                print(f"  ⚠️ Unknown: {face['confidence']:.1f}%")
    else:
        print("No humans detected")
    
    return result


# ==================== QUICK START 2: Register Person ====================

def quick_start_register():
    """Register a new person with just 2 lines"""
    
    from ai.detect import register_face
    
    # Take a photo and register
    with open('person_photo.jpg', 'rb') as f:
        result = register_face(f.read(), 'John Doe')
    
    if result['success']:
        print(f"✅ Registered: {result['message']}")
    else:
        print(f"❌ Error: {result['message']}")


# ==================== QUICK START 3: Flask Endpoint ====================

def quick_start_flask():
    """Complete Flask endpoint with face detection and alerts"""
    
    code = """
from flask import Flask, request, jsonify
from ai.detect import detect_and_recognize_faces
from ai.telegram_alerts import handle_detection_alert

app = Flask(__name__)

@app.route('/detect', methods=['POST'])
def detect_motion():
    image_bytes = request.files['image'].read()
    result = detect_and_recognize_faces(image_bytes)
    handle_detection_alert(result)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
    """
    
    print(code)


# ==================== QUICK START 4: Check Registered Faces ====================

def quick_start_list_faces():
    """See all registered people"""
    
    from ai.detect import list_known_faces
    
    faces = list_known_faces()
    
    if not faces:
        print("No registered faces yet")
        return
    
    print(f"Registered persons ({len(faces)}):")
    for face_id, data in faces.items():
        print(f"  • {data['name']}")


# ==================== QUICK START 5: Remove Person ====================

def quick_start_remove():
    """Remove a person from database"""
    
    from ai.detect import list_known_faces, remove_face
    
    faces = list_known_faces()
    
    if faces:
        # Remove first person
        face_id = list(faces.keys())[0]
        name = faces[face_id]['name']
        
        if remove_face(face_id):
            print(f"✅ Removed: {name}")


# ==================== QUICK START 6: Multi-Camera Setup ====================

def quick_start_multi_camera():
    """Handle multiple cameras with proper alerts"""
    
    code = """
from ai.detect import detect_and_recognize_faces
from ai.telegram_alerts import handle_detection_alert

# Camera 1
image1 = request.files['image1'].read()
result1 = detect_and_recognize_faces(image1)
handle_detection_alert(result1, camera_id='Front Door')

# Camera 2
image2 = request.files['image2'].read()
result2 = detect_and_recognize_faces(image2)
handle_detection_alert(result2, camera_id='Back Yard')
    """
    
    print(code)


# ==================== QUICK START 7: Initialize System ====================

def quick_start_init():
    """One-time system initialization"""
    
    from ai.detect import init_detector
    
    # Initialize
    detector = init_detector()
    
    # Create Rekognition collection (one-time)
    if detector.create_collection():
        print("✅ Face collection ready")
    
    # Register your face
    with open('admin_face.jpg', 'rb') as f:
        detector.register_face(f.read(), 'Admin')
        print("✅ Admin registered")


# ==================== QUICK START 8: Monitor Unknown Faces ====================

def quick_start_unknown_faces():
    """Find and review unknown faces detected"""
    
    import os
    from pathlib import Path
    
    unknown_dir = 'unknown_faces'
    
    files = list(Path(unknown_dir).glob('*.jpg'))
    print(f"Unknown faces saved: {len(files)}")
    
    for file in files:
        print(f"  📷 {file.name}")


# ==================== QUICK START 9: Test Detection ====================

def quick_start_test():
    """Test the system with a sample image"""
    
    code = """
# 1. Save a test image to 'test.jpg'

# 2. Run this:
from ai.detect import detect_and_recognize_faces

with open('test.jpg', 'rb') as f:
    result = detect_and_recognize_faces(f.read())

print(f"Humans detected: {result['human_detected']}")
print(f"Faces found: {len(result['faces'])}")

for i, face in enumerate(result['faces']):
    print(f"  Face {i+1}: {face['status']} ({face['confidence']:.1f}%)")
    """
    
    print(code)


# ==================== QUICK START 10: Alert with Confidence ====================

def quick_start_smart_alerts():
    """Send alerts only for high-confidence detections"""
    
    code = """
from ai.detect import detect_and_recognize_faces
from ai.telegram_alerts import handle_detection_alert

image_bytes = request.files['image'].read()
result = detect_and_recognize_faces(image_bytes)

# Alert only for high-confidence detections
for face in result['faces']:
    if face['confidence'] < 85:  # Skip low confidence
        continue
    
    handle_detection_alert({'faces': [face]})
    """
    
    print(code)


# ==================== CHEAT SHEET ====================

CHEAT_SHEET = """
╔════════════════════════════════════════════════════════════════╗
║            FACE DETECTION SYSTEM - CHEAT SHEET                 ║
╚════════════════════════════════════════════════════════════════╝

DETECT FACES:
  from ai.detect import detect_and_recognize_faces
  result = detect_and_recognize_faces(image_bytes)

REGISTER PERSON:
  from ai.detect import register_face
  register_face(image_bytes, 'Name')

LIST REGISTERED:
  from ai.detect import list_known_faces
  faces = list_known_faces()

REMOVE PERSON:
  from ai.detect import remove_face
  remove_face(face_id)

SEND ALERT:
  from ai.telegram_alerts import handle_detection_alert
  handle_detection_alert(result, camera_id='CAMERA_NAME')

CHECK COLLECTION:
  from ai.detect import get_collection_stats
  stats = get_collection_stats()

RESULT STRUCTURE:
  {
    "human_detected": bool,
    "faces": [
      {
        "status": "KNOWN/UNKNOWN",
        "name": "John",           # Only for KNOWN
        "confidence": 98.5,
        "bbox": {x, y, width, height}
      }
    ]
  }

ALERT MESSAGES:
  ✅ KNOWN: Known person detected
  ⚠️ UNKNOWN: Stranger detected

ERROR HANDLING:
  if result.get('error'):
      print(f"Detection failed: {result['error']}")

MULTI-CAMERA:
  result1 = detect_and_recognize_faces(image1)
  handle_detection_alert(result1, camera_id='Front')

UNKNOWN FACES DIRECTORY:
  ./unknown_faces/
  (saved automatically for review)

CONFIGURATION:
  Edit backend/config.py:
  - AWS_FACE_MATCH_THRESHOLD (0-100)
  - AWS_FACE_SIMILARITY_THRESHOLD (0-100)
  - AWS_FACE_COLLECTION_ID
  - AWS_UNKNOWN_FACES_DIR

════════════════════════════════════════════════════════════════
"""


if __name__ == '__main__':
    print(CHEAT_SHEET)
    print("\nRun individual quick starts:\n")
    print("  quick_start_detection()      - Detect faces")
    print("  quick_start_register()       - Register person")
    print("  quick_start_list_faces()     - See registered")
    print("  quick_start_remove()         - Remove person")
    print("  quick_start_init()           - Initialize system")
    print("  quick_start_test()           - Test with image")
    print("\nExample: python quick_start.py")
