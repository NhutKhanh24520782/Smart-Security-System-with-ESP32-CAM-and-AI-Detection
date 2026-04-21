"""
Example usage of AWS Rekognition face detection and recognition system.

This demonstrates how to:
1. Initialize the detector
2. Register known faces
3. Detect and recognize faces in images
4. Manage the face collection
"""

import logging
from detect import (
    init_detector,
    detect_and_recognize_faces,
    register_face,
    remove_face,
    list_known_faces,
    get_collection_stats
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_initialization():
    """Example 1: Initialize the detector and create collection"""
    print("\n=== Example 1: Initialization ===")
    
    detector = init_detector()
    logger.info("Detector initialized")
    
    # Create face collection
    success = detector.create_collection()
    if success:
        logger.info("Face collection created successfully")
    
    # Get collection stats
    stats = detector.get_collection_stats()
    print(f"Collection Stats: {stats}")


def example_register_faces():
    """Example 2: Register known faces"""
    print("\n=== Example 2: Register Known Faces ===")
    
    # Simulate reading image bytes
    # In real usage: image_bytes = open('person_photo.jpg', 'rb').read()
    
    sample_images = {
        'john_doe.jpg': 'John Doe',
        'jane_smith.jpg': 'Jane Smith',
        'admin_user.jpg': 'Admin'
    }
    
    for image_file, person_name in sample_images.items():
        try:
            # Simulate reading image
            with open(image_file, 'rb') as f:
                image_bytes = f.read()
            
            result = register_face(image_bytes, person_name)
            if result['success']:
                logger.info(f"✅ Registered {person_name}: {result['face_id']}")
            else:
                logger.error(f"❌ Failed to register {person_name}: {result['message']}")
        
        except FileNotFoundError:
            logger.warning(f"Image file not found: {image_file} (skipping for example)")


def example_list_known_faces():
    """Example 3: List all known faces"""
    print("\n=== Example 3: List Known Faces ===")
    
    faces = list_known_faces()
    if faces:
        print(f"Total known faces: {len(faces)}\n")
        for face_id, data in faces.items():
            print(f"  Face ID: {face_id}")
            print(f"  Name: {data['name']}")
            print(f"  Registered: {data['registered_at']}")
            print(f"  Confidence: {data['confidence']:.2f}%\n")
    else:
        logger.info("No known faces registered yet")


def example_detect_faces_in_image():
    """Example 4: Detect and recognize faces in an image"""
    print("\n=== Example 4: Detect and Recognize Faces ===")
    
    try:
        # Simulate reading a captured image from ESP32
        # In real usage: image_bytes = request.files['image'].read()
        with open('test_image.jpg', 'rb') as f:
            image_bytes = f.read()
        
        # Detect and recognize faces
        result = detect_and_recognize_faces(image_bytes)
        
        print(f"\nHuman Detected: {result['human_detected']}")
        print(f"Total Faces: {len(result['faces'])}\n")
        
        for i, face in enumerate(result['faces'], 1):
            print(f"Face {i}:")
            print(f"  Status: {face['status']}")
            
            if face['status'] == 'KNOWN':
                print(f"  Name: {face['name']}")
            
            print(f"  Confidence: {face['confidence']:.2f}%")
            
            if 'bbox' in face:
                bbox = face['bbox']
                print(f"  Position: x={bbox['x']:.3f}, y={bbox['y']:.3f}, "
                      f"w={bbox['width']:.3f}, h={bbox['height']:.3f}")
            print()
    
    except FileNotFoundError:
        logger.warning("Test image not found (skipping for example)")


def example_telegram_alert_integration():
    """Example 5: Integration with Telegram alerts"""
    print("\n=== Example 5: Telegram Alert Integration ===")
    
    # This demonstrates how to use face detection results for Telegram alerts
    
    def generate_telegram_alert(detection_result):
        """Generate a telegram alert based on detection result"""
        
        if not detection_result['human_detected']:
            return None  # No humans detected, no alert
        
        alerts = []
        
        for face in detection_result['faces']:
            if face['status'] == 'KNOWN':
                message = f"✅ Known person detected: {face['name']}"
                confidence = face['confidence']
                alerts.append({
                    'type': 'KNOWN',
                    'message': message,
                    'confidence': confidence
                })
            else:
                message = f"⚠️ Stranger detected (Confidence: {face['confidence']:.1f}%)"
                alerts.append({
                    'type': 'UNKNOWN',
                    'message': message,
                    'confidence': face['confidence']
                })
        
        return alerts
    
    # Example usage
    example_detection = {
        'human_detected': True,
        'faces': [
            {'status': 'KNOWN', 'name': 'John Doe', 'confidence': 98.5},
            {'status': 'UNKNOWN', 'confidence': 87.2}
        ]
    }
    
    alerts = generate_telegram_alert(example_detection)
    print("\nGenerated Alerts:")
    for alert in alerts:
        print(f"  [{alert['type']}] {alert['message']}")


def example_face_management():
    """Example 6: Face management operations"""
    print("\n=== Example 6: Face Management ===")
    
    faces = list_known_faces()
    
    if faces:
        # Example: Rename a person
        first_face_id = list(faces.keys())[0]
        logger.info(f"Example: Renaming face {first_face_id}")
        # detector.rename_person(first_face_id, "New Name")
        
        # Example: Remove a face
        logger.info(f"Example: To remove a face use remove_face('{first_face_id}')")


# ==================== Integration with Flask Backend ====================

def setup_flask_integration():
    """
    Example of integrating face detection with Flask backend.
    
    This would be used in your Flask app.py:
    """
    
    flask_integration_code = """
    from flask import Flask, request, jsonify
    from ai.detect import detect_and_recognize_faces
    
    app = Flask(__name__)
    
    @app.route('/detect', methods=['POST'])
    def detect_motion():
        '''
        Receive image from ESP32 and perform face detection/recognition.
        '''
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        image_bytes = image_file.read()
        
        # Detect and recognize faces
        result = detect_and_recognize_faces(image_bytes)
        
        # Generate Telegram alert
        if result['human_detected']:
            for face in result['faces']:
                if face['status'] == 'UNKNOWN':
                    send_telegram_alert(f"⚠️ Stranger detected! Confidence: {face['confidence']:.1f}%")
                else:
                    send_telegram_alert(f"✅ Known person: {face['name']}")
        
        return jsonify(result), 200
    
    @app.route('/register', methods=['POST'])
    def register_new_person():
        '''
        Register a new known person (admin endpoint).
        '''
        if 'image' not in request.files or 'name' not in request.form:
            return jsonify({'error': 'Missing image or name'}), 400
        
        image_bytes = request.files['image'].read()
        person_name = request.form['name']
        
        result = register_face(image_bytes, person_name)
        return jsonify(result), 201
    
    @app.route('/faces', methods=['GET'])
    def get_known_faces():
        '''
        Get list of all registered faces (admin endpoint).
        '''
        faces = list_known_faces()
        return jsonify(faces), 200
    
    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5002, debug=False)
    """
    
    print("\n=== Flask Integration Example ===")
    print(flask_integration_code)


if __name__ == '__main__':
    print("AWS Rekognition Face Detection & Recognition - Usage Examples")
    print("=" * 60)
    
    # Run examples
    example_basic_initialization()
    example_register_faces()
    example_list_known_faces()
    example_detect_faces_in_image()
    example_telegram_alert_integration()
    example_face_management()
    setup_flask_integration()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
