from flask import Flask, request, jsonify
import logging
import os
from datetime import datetime
from ai.detect import detect_and_recognize_faces
from services.telegram import send_alert
from coordination.coordinator import MultiCameraCoordinator
from mqtt_client import init_mqtt
from config import (
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG,
    LOG_LEVEL, LOG_FILE, IMAGE_SAVE_PATH, SAVE_IMAGES
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Ensure image save directory exists
if SAVE_IMAGES and not os.path.exists(IMAGE_SAVE_PATH):
    os.makedirs(IMAGE_SAVE_PATH)

coordinator = MultiCameraCoordinator()
mqtt_client_instance = None

@app.route('/status', methods=['GET'])
def get_status():
    """Get backend status including MQTT connection and connected ESP32 devices"""
    mqtt_connected = False
    esp32_devices = []
    
    if mqtt_client_instance:
        mqtt_connected = mqtt_client_instance.client.is_connected()
        esp32_devices = list(mqtt_client_instance.connected_esp32_devices)
    
    return jsonify({
        'status': 'online',
        'service': 'Smart Security System Backend',
        'version': '1.0.0',
        'mqtt': {
            'connected': mqtt_connected,
            'broker': os.environ.get('MQTT_BROKER_HOST', 'configured'),
            'subscribed_topic': 'camera/+/motion'
        },
        'esp32_devices': {
            'total': len(esp32_devices),
            'devices': esp32_devices
        }
    }), 200

@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Endpoint to receive image uploads from ESP32-CAM devices
    """
    try:
        # Get device_id and image file
        device_id = request.form.get('device_id')
        image_file = request.files.get('image')

        if not device_id or not image_file:
            logger.warning("Missing device_id or image in request")
            return jsonify({'error': 'Missing device_id or image'}), 400

        # Read image bytes
        image_bytes = image_file.read()

        # Save image locally if enabled
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if SAVE_IMAGES:
            filename = f"{device_id}_{timestamp}.jpg"
            filepath = os.path.join(IMAGE_SAVE_PATH, filename)
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            logger.info(f"Image saved: {filepath}")

        # Perform human detection
        logger.info(f"Processing image from {device_id}")
        detection_result = detect_and_recognize_faces(image_bytes)
        
        # Extract human_detected and confidence from new format
        human_detected = detection_result.get('human_detected', False)
        # Use highest confidence face as overall confidence
        confidence = 0.0
        if detection_result.get('faces'):
            confidence = max(face.get('confidence', 0.0) for face in detection_result['faces'])

        if human_detected:
            logger.info(f"Human detected by {device_id} (confidence={confidence}), sending alert")
            alert = coordinator.add_detection(device_id, datetime.now(), confidence)
            if alert:
                send_alert(device_id, image_bytes, alert['message'])
        else:
            logger.info(f"No human detected in image from {device_id}")

        # Send face-specific alerts using new system
        from ai.telegram_alerts import handle_detection_alert
        handle_detection_alert(detection_result, device_id)

        return jsonify({
            'status': 'success',
            'device_id': device_id,
            'human_detected': human_detected,
            'confidence': confidence,
            'timestamp': timestamp,
            'faces': detection_result.get('faces', [])
        }), 200

    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with system info"""
    return jsonify({
        'service': 'Smart Security System Backend',
        'version': '1.0.0',
        'endpoints': {
            'upload': '/upload (POST)',
            'health': '/health (GET)',
            'status': '/status (GET)',
            'root': '/ (GET)'
        }
    }), 200

if __name__ == '__main__':
    logger.info("Starting Smart Security System Backend")
    mqtt_client_instance = init_mqtt(coordinator)
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, use_reloader=False)