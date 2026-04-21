import json
import logging
import requests
from datetime import datetime
import paho.mqtt.client as mqtt
from ai.detect import detect_and_recognize_faces
from coordination.coordinator import MultiCameraCoordinator
from services.telegram import send_alert
from config import (
    MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_USERNAME,
    MQTT_PASSWORD, MQTT_TOPIC_FILTER, MQTT_KEEPALIVE, MQTT_DEBUG,
    SAVE_IMAGES, IMAGE_SAVE_PATH
)

logger = logging.getLogger(__name__)

class MqttBackendClient:
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.client = mqtt.Client()
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.last_message_id = None  # Prevent duplicate processing
        self.duplicate_window = 1.0  # 1 second window to detect duplicates
        self.connected_esp32_devices = set()  # Track connected ESP32 devices
        
        # Enable TLS for secure connection (port 8883)
        if MQTT_BROKER_PORT == 8883:
            self.client.tls_set()
            logger.info("MQTT TLS enabled for secure connection")
        
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def start(self):
        logger.info(f"Connecting to MQTT broker {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        # Reconnect automatically if disconnected
        self.client.reconnect_delay_set(min_delay=1, max_delay=32)
        self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEPALIVE)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"✅ MQTT connected successfully to {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
            result = self.client.subscribe(MQTT_TOPIC_FILTER)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📡 MQTT subscribed to topic pattern: {MQTT_TOPIC_FILTER}")
                logger.info(f"   Waiting for motion events from ESP32 cameras...")
            else:
                logger.warning(f"   Subscribe failed with result: {result}")
        else:
            logger.error(f"❌ MQTT connection failed with rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        logger.warning(f"⚠️  MQTT disconnected (rc={rc})")
        self.connected_esp32_devices.clear()

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            data = json.loads(payload)
            device_id = data.get('device_id')
            timestamp_str = data.get('timestamp')
            motion = data.get('motion')

            # Create message signature for duplicate detection
            msg_signature = f"{device_id}_{timestamp_str}"
            if msg_signature == self.last_message_id:
                logger.debug(f"⚠️ Duplicate MQTT message ignored: {device_id}")
                return
            self.last_message_id = msg_signature

            logger.info(f"📨 MQTT message received from topic '{msg.topic}'")
            logger.debug(f"   Payload: {payload}")
            
            # ✅ Mới: Chỉ expect device_id, timestamp, motion (không image)
            if not device_id or not timestamp_str or motion is None:
                logger.warning(f"❌ MQTT message missing required fields: {data}")
                return

            timestamp = datetime.fromisoformat(timestamp_str)
            
            if not motion:
                logger.debug(f"Motion is false for {device_id}, skipping")
                return

            # Track ESP32 device
            if device_id not in self.connected_esp32_devices:
                self.connected_esp32_devices.add(device_id)
                logger.info(f"🔌 New ESP32 device detected: {device_id}")

            logger.info(f"🔴 Motion event received from {device_id}")
            esp32_ip = data.get("ip")
            if esp32_ip:
                logger.info(f"   ESP32 IP: {esp32_ip}")
            logger.info(f"   Timestamp: {timestamp_str}")
            
            logger.info(f"🔴 Fetching image via HTTP from {device_id}...")
            
            # ✅ Gọi HTTP endpoint trên ESP32 để lấy ảnh (IP từ MQTT message)
            image_bytes = self._fetch_image_from_esp32(device_id, data)
            if not image_bytes:
                logger.warning(f"❌ Failed to fetch image from {device_id}")
                return

            if SAVE_IMAGES:
                self._save_local_image(device_id, image_bytes, timestamp)

            logger.info(f"🧠 Running AI detection on image from {device_id}")
            detection_result = detect_and_recognize_faces(image_bytes)
            
            # Extract human_detected and confidence from new format
            human_detected = detection_result.get('human_detected', False)
            confidence = 0.0
            if detection_result.get('faces'):
                confidence = max(face.get('confidence', 0.0) for face in detection_result['faces'])

            if human_detected:
                logger.info(f"✅ Human detected by {device_id} (confidence={confidence:.2f})")
                alert = self.coordinator.add_detection(device_id, timestamp, confidence)
                if alert:
                    logger.info(f"🚨 Sending alert: {alert['message']}")
                    send_alert(device_id, image_bytes, alert['message'])
            else:
                logger.info(f"❌ No human detected for {device_id}")

            # Send face-specific alerts using new system
            from ai.telegram_alerts import handle_detection_alert
            handle_detection_alert(detection_result, device_id)

        except Exception as exc:
            logger.error(f"❌ Failed to handle MQTT message: {exc}", exc_info=True)

    def _fetch_image_from_esp32(self, device_id, data):
        """Fetch image from ESP32 HTTP server with retry"""
        esp32_ip = data.get("ip")
        
        if not esp32_ip:
            logger.warning(f"❌ Missing IP in MQTT message from {device_id}")
            return None
        
        url = f"http://{esp32_ip}:80/capture"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"   🔗 HTTP GET {url} (attempt {attempt + 1}/{max_retries})...")
                response = requests.get(url, timeout=3)
                
                if response.status_code == 200:
                    image_bytes = response.content
                    logger.info(f"   ✅ Image fetched: {len(image_bytes)} bytes")
                    return image_bytes
                else:
                    logger.warning(f"   ⚠️  HTTP {response.status_code} (attempt {attempt + 1}/{max_retries})")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"   ⚠️  Timeout (attempt {attempt + 1}/{max_retries})")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"   ⚠️  Connection error: {e} (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.warning(f"   ⚠️  {type(e).__name__}: {e} (attempt {attempt + 1}/{max_retries})")
            
            # Delay before retry
            if attempt < max_retries - 1:
                import time
                time.sleep(0.5)
        
        logger.error(f"   ❌ Failed to fetch image from {device_id} after {max_retries} retries")
        return None

    def _save_local_image(self, device_id, image_bytes, timestamp):
        filename = f"{device_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        path = f"{IMAGE_SAVE_PATH}/{filename}"
        try:
            with open(path, 'wb') as f:
                f.write(image_bytes)
            logger.info(f"Saved MQTT image locally: {path}")
        except Exception as exc:
            logger.error(f"Failed to save image locally: {exc}")

mqtt_client = None

def init_mqtt(coordinator):
    global mqtt_client
    mqtt_client = MqttBackendClient(coordinator)
    mqtt_client.start()
    return mqtt_client
