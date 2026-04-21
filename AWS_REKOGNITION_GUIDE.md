# AWS Rekognition Face Detection & Recognition Implementation

Complete guide for the upgraded ESP32-CAM security system with AWS Rekognition face detection and recognition.

## 📋 Overview

This implementation adds intelligent face detection and recognition to your ESP32-CAM security system:

- **Face Detection**: Detects faces in incoming images
- **Face Recognition**: Matches detected faces against a collection of known persons
- **Person Management**: Register, update, and manage known faces
- **Telegram Alerts**: Send smart alerts based on detection results
- **Local Storage**: Save unknown faces for later review
- **Error Handling**: Robust error handling and logging

## 📁 Files Modified/Created

### Modified Files
1. **[backend/config.py](backend/config.py)** - Added AWS Rekognition configuration
2. **[backend/ai/detect.py](backend/ai/detect.py)** - Complete rewrite with face detection/recognition

### New Files
1. **[backend/ai/example_usage.py](backend/ai/example_usage.py)** - Usage examples and Flask integration
2. **[backend/ai/telegram_alerts.py](backend/ai/telegram_alerts.py)** - Telegram alert helper

## ⚙️ Configuration

### config.py Settings

```python
# AWS Rekognition Face Recognition settings
AWS_FACE_COLLECTION_ID = 'smart-security-collection'      # Rekognition collection name
AWS_FACE_MATCH_THRESHOLD = 80.0                            # Confidence threshold (0-100)
AWS_FACE_SIMILARITY_THRESHOLD = 80.0                       # Similarity threshold (0-100)
AWS_KNOWN_FACES_DB = 'known_faces.json'                   # Local face database file
AWS_UNKNOWN_FACES_DIR = 'unknown_faces/'                  # Directory for unknown face images
```

### AWS Setup

Ensure your AWS credentials are configured in `config.py`:
```python
AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY = 'your-aws-access-key'
AWS_SECRET_KEY = 'your-aws-secret-key'
```

## 🚀 Core Features

### 1. Face Detection

Detect all faces in an image with confidence scores and bounding boxes:

```python
from ai.detect import detect_and_recognize_faces

# Read image from ESP32
image_bytes = open('snapshot.jpg', 'rb').read()

# Detect and recognize faces
result = detect_and_recognize_faces(image_bytes)

# Result structure:
# {
#     "human_detected": True,
#     "faces": [
#         {
#             "status": "KNOWN",
#             "name": "John Doe",
#             "confidence": 98.5,
#             "bbox": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4}
#         },
#         {
#             "status": "UNKNOWN",
#             "confidence": 87.2,
#             "bbox": {"x": 0.6, "y": 0.1, "width": 0.25, "height": 0.35}
#         }
#     ]
# }
```

### 2. Face Recognition

Automatically matches detected faces against known persons:
- **KNOWN**: Face matches a registered person → displays name
- **UNKNOWN**: Face doesn't match any registered person → saves for review

```python
# Detect result automatically includes recognition status
for face in result['faces']:
    if face['status'] == 'KNOWN':
        print(f"✅ Known person: {face['name']}")
    else:
        print(f"⚠️ Unknown person (confidence: {face['confidence']}%)")
```

### 3. Person Registration

Register new known persons:

```python
from ai.detect import register_face

# Register a person
image_bytes = open('john_doe.jpg', 'rb').read()
result = register_face(image_bytes, 'John Doe')

if result['success']:
    print(f"✅ Registered: {result['face_id']}")
else:
    print(f"❌ Error: {result['message']}")
```

### 4. Person Management

Complete person management functionality:

```python
from ai.detect import (
    list_known_faces,
    remove_face,
    get_collection_stats
)

# List all known faces
faces = list_known_faces()
for face_id, data in faces.items():
    print(f"{data['name']}: {face_id}")

# Remove a person
remove_face('face-id-12345')

# Get collection statistics
stats = get_collection_stats()
print(f"Total faces: {stats['face_count']}")
```

## 📱 Telegram Integration

### Automated Alerts

The system automatically sends Telegram alerts based on detection results:

```python
from ai.telegram_alerts import handle_detection_alert

# After detecting faces
detection_result = detect_and_recognize_faces(image_bytes)

# Send Telegram alerts
alerts = handle_detection_alert(detection_result, camera_id='CAM-1')
```

### Alert Messages

**Known Person Detected:**
```
✅ Known Person Detected
Name: John Doe
Confidence: 98.5% [Camera: CAM-1]
```

**Stranger Detected:**
```
⚠️ STRANGER DETECTED ⚠️
Confidence: 87.2% [Camera: CAM-1]
This is an unknown person. Check security footage!
```

## 🔌 Flask Integration Example

Complete Flask endpoint for receiving images from ESP32:

```python
from flask import Flask, request, jsonify
from ai.detect import detect_and_recognize_faces, register_face
from ai.telegram_alerts import handle_detection_alert

app = Flask(__name__)

@app.route('/detect', methods=['POST'])
def detect_motion():
    """Receive image from ESP32 and perform face detection"""
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    image_bytes = request.files['image'].read()
    camera_id = request.form.get('camera_id', 'CAM-1')
    
    # Detect and recognize faces
    detection_result = detect_and_recognize_faces(image_bytes)
    
    # Send Telegram alerts
    alerts = handle_detection_alert(detection_result, camera_id)
    
    # Save image if humans detected
    if detection_result['human_detected']:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captured_images/{camera_id}_{timestamp}.jpg"
        with open(filename, 'wb') as f:
            f.write(image_bytes)
    
    return jsonify({
        'detection': detection_result,
        'alerts_sent': len(alerts)
    }), 200


@app.route('/register', methods=['POST'])
def register_new_person():
    """Register a new known person (admin endpoint)"""
    
    if 'image' not in request.files or 'name' not in request.form:
        return jsonify({'error': 'Missing image or name'}), 400
    
    image_bytes = request.files['image'].read()
    person_name = request.form['name']
    
    result = register_face(image_bytes, person_name)
    return jsonify(result), 201 if result['success'] else 400


@app.route('/faces', methods=['GET'])
def get_known_faces():
    """Get list of registered faces (admin endpoint)"""
    
    faces = list_known_faces()
    return jsonify({
        'count': len(faces),
        'faces': faces
    }), 200
```

## 📊 Data Structures

### Detection Result

```python
{
    "human_detected": bool,
    "faces": [
        {
            "status": "KNOWN" | "UNKNOWN",
            "name": str,              # Only for KNOWN faces
            "confidence": float,      # Detection confidence (0-100)
            "bbox": {
                "x": float,           # Normalized position (0-1)
                "y": float,
                "width": float,
                "height": float
            }
        }
    ],
    "error": str                      # Optional, if error occurred
}
```

### Known Faces Database

File: `known_faces.json`

```json
{
    "face-id-uuid-1234": {
        "name": "John Doe",
        "registered_at": "2024-04-20T10:30:45.123456",
        "confidence": 99.5
    },
    "face-id-uuid-5678": {
        "name": "Jane Smith",
        "registered_at": "2024-04-20T11:15:20.654321",
        "confidence": 98.2
    }
}
```

## 🔧 API Reference

### Face Detection & Recognition

#### `detect_and_recognize_faces(image_bytes) → dict`
Detect and recognize faces in an image.
- **Args**: `image_bytes` (bytes) - JPEG image data
- **Returns**: Detection result with faces list

#### `register_face(image_bytes, person_name) → dict`
Register a new face to the collection.
- **Args**: `image_bytes` (bytes), `person_name` (str)
- **Returns**: `{"success": bool, "face_id": str, "message": str, "confidence": float}`

#### `remove_face(face_id) → bool`
Remove a person from the collection.
- **Args**: `face_id` (str)
- **Returns**: True if successful

#### `list_known_faces() → dict`
Get all registered faces.
- **Returns**: `{face_id: {"name": str, "registered_at": str, "confidence": float}}`

#### `get_collection_stats() → dict`
Get collection statistics.
- **Returns**: `{"collection_id": str, "face_count": int, "known_faces_in_db": int}`

### Telegram Alerts

#### `handle_detection_alert(detection_result, camera_id=None) → list`
Send Telegram alerts based on detection result.
- **Args**: Detection result, optional camera ID
- **Returns**: List of sent alerts

## 🛠️ Setup Steps

### 1. Install Dependencies

```bash
pip install boto3
```

### 2. Configure AWS Credentials

Edit `config.py`:
```python
AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY = 'your-key'
AWS_SECRET_KEY = 'your-secret'
```

### 3. Initialize Collection

```python
from ai.detect import init_detector

detector = init_detector()
detector.create_collection()  # Creates AWS Rekognition collection
```

### 4. Register Known Faces

```python
from ai.detect import register_face

with open('john.jpg', 'rb') as f:
    register_face(f.read(), 'John Doe')
```

### 5. Start Detection

The system will now automatically:
- Detect faces when images arrive
- Recognize known persons
- Send Telegram alerts
- Save unknown faces

## 📝 Logging

The system uses Python's logging module. Configure in your Flask app:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_system.log'),
        logging.StreamHandler()
    ]
)
```

Log messages include:
- Face detection results
- Person registration/removal
- Telegram alert sends
- Unknown face storage
- AWS API errors
- Configuration issues

## ⚠️ Error Handling

The system handles common errors:

| Error | Handling |
|-------|----------|
| Collection doesn't exist | Returns `None` from search functions |
| No faces in image | Returns empty faces list |
| Image quality too low | AWS rejects during indexing |
| AWS credentials invalid | Raises exception at initialization |
| File system errors | Logs warning, continues operation |

## 🔒 Security Considerations

1. **AWS Credentials**: Store securely, never commit to repo
2. **Face Data**: Local `known_faces.json` contains FaceIds (safe, not actual images)
3. **Unknown Faces**: Stored locally for review, consider governance policy
4. **Telegram Token**: Store securely in config
5. **Collection Privacy**: Use private AWS account

## 📊 Performance Notes

- Face detection: ~1-2 seconds per image (AWS API)
- Face recognition: ~200ms per face against collection
- Optimal image size: 720p or higher
- Recommended face size in image: 100x100+ pixels

## 🧪 Testing

Run example usage:

```bash
cd backend/ai
python example_usage.py
```

## 📚 Additional Resources

- [AWS Rekognition Documentation](https://docs.aws.amazon.com/rekognition/)
- [boto3 Rekognition API](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rekognition.html)
- [ESP32-CAM Setup Guide](https://github.com/espressif/esp32-camera)

## 🐛 Troubleshooting

### "No matching face found"
- Ensure face collection is initialized: `detector.create_collection()`
- Register at least one face: `register_face(...)`
- Check AWS credentials in config

### "Image quality too low"
- Use `quality=92` or higher in ESP32 camera settings
- Ensure adequate lighting
- Camera resolution should be 800x600 or higher

### "AWS API errors"
- Verify credentials are correct
- Check AWS Region is accessible
- Ensure Rekognition service is enabled in AWS console

### "Unknown faces not saving"
- Check permissions on `unknown_faces/` directory
- Verify `AWS_UNKNOWN_FACES_DIR` path in config

## 📝 License

This implementation is part of the Smart Security System project.
