"""
Telegram Alert Helper for Face Detection Integration

This module handles sending alerts to Telegram based on face detection results.
"""

import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from services.telegram import TelegramBot

logger = logging.getLogger(__name__)


class FaceAlertManager:
    """Manages Telegram alerts based on face detection results"""
    
    def __init__(self):
        self.telegram = TelegramBot()
        self.last_unknown_face_time = {}  # Track last unknown face alert per camera
        self.alert_cooldown_seconds = 30  # Don't spam alerts
    
    def handle_detection_result(self, detection_result, camera_id=None):
        """
        Process detection result and send appropriate Telegram alerts.
        
        Args:
            detection_result: Result from detect_and_recognize_faces()
            camera_id: Optional camera identifier for multi-camera setups
        
        Returns:
            list: List of sent alerts
        """
        alerts_sent = []
        
        if not detection_result.get('human_detected'):
            return alerts_sent
        
        faces = detection_result.get('faces', [])
        
        for face in faces:
            if face['status'] == 'KNOWN':
                alert = self._create_known_alert(face, camera_id)
                if self.telegram.send_message(alert['message'], alert.get('emoji')):
                    alerts_sent.append(alert)
                    logger.info(f"Alert sent: {alert['type']}")
            
            elif face['status'] == 'UNKNOWN':
                alert = self._create_unknown_alert(face, camera_id)
                # Only send unknown face alerts with cooldown
                if self._should_send_alert(camera_id):
                    if self.telegram.send_message(alert['message'], alert.get('emoji')):
                        alerts_sent.append(alert)
                        logger.info(f"Alert sent: {alert['type']}")
                        self._update_alert_time(camera_id)
        
        return alerts_sent
    
    def _create_known_alert(self, face, camera_id):
        """Create alert message for known person"""
        name = face.get('name', 'Unknown')
        confidence = face.get('confidence', 0)
        
        camera_info = f" [Camera: {camera_id}]" if camera_id else ""
        message = (
            f"✅ *Known Person Detected*\n"
            f"Name: `{name}`\n"
            f"Confidence: `{confidence:.1f}%`{camera_info}"
        )
        
        return {
            'type': 'KNOWN_PERSON',
            'message': message,
            'emoji': '✅',
            'name': name,
            'confidence': confidence
        }
    
    def _create_unknown_alert(self, face, camera_id):
        """Create alert message for unknown person"""
        confidence = face.get('confidence', 0)
        
        camera_info = f" [Camera: {camera_id}]" if camera_id else ""
        message = (
            f"⚠️ *STRANGER DETECTED* ⚠️\n"
            f"Confidence: `{confidence:.1f}%`{camera_info}\n"
            f"This is an unknown person. Check security footage!"
        )
        
        return {
            'type': 'UNKNOWN_PERSON',
            'message': message,
            'emoji': '⚠️',
            'confidence': confidence
        }
    
    def _should_send_alert(self, camera_id):
        """Check if enough time has passed since last unknown face alert"""
        import time
        
        if camera_id not in self.last_unknown_face_time:
            return True
        
        time_since_last = time.time() - self.last_unknown_face_time[camera_id]
        return time_since_last >= self.alert_cooldown_seconds
    
    def _update_alert_time(self, camera_id):
        """Update the last alert time for a camera"""
        import time
        self.last_unknown_face_time[camera_id] = time.time()
    
    def send_debug_alert(self, message):
        """Send debug/info message"""
        return self.telegram.send_message(f"🔧 {message}")
    
    def send_error_alert(self, error_message):
        """Send error alert"""
        return self.telegram.send_message(f"❌ *Error*: {error_message}")


# Global instance
alert_manager = None


def init_alert_manager():
    """Initialize the global alert manager"""
    global alert_manager
    if alert_manager is None:
        alert_manager = FaceAlertManager()
    return alert_manager


def handle_detection_alert(detection_result, camera_id=None):
    """
    Convenience function to handle alerts for a detection result.
    
    Args:
        detection_result: Result from detect_and_recognize_faces()
        camera_id: Optional camera identifier
    
    Returns:
        list: List of sent alerts
    """
    global alert_manager
    if alert_manager is None:
        alert_manager = init_alert_manager()
    
    return alert_manager.handle_detection_result(detection_result, camera_id)


# ==================== Integration Example ====================

def example_flask_integration():
    """
    Example of integrating face detection and Telegram alerts in Flask.
    
    Add this to your app.py or main detection route:
    """
    
    integration_code = '''
    from flask import Flask, request, jsonify
    from ai.detect import detect_and_recognize_faces
    from ai.telegram_alerts import handle_detection_alert
    
    @app.route('/detect', methods=['POST'])
    def detect_motion():
        """Receive image from ESP32 and send Telegram alerts"""
        
        image_bytes = request.files['image'].read()
        camera_id = request.form.get('camera_id', 'CAM-1')
        
        # Detect and recognize faces
        detection_result = detect_and_recognize_faces(image_bytes)
        logger.info(f"Detection result: {detection_result}")
        
        # Send Telegram alerts
        alerts = handle_detection_alert(detection_result, camera_id)
        
        return jsonify({
            'detection': detection_result,
            'alerts_sent': len(alerts)
        }), 200
    '''
    
    return integration_code
