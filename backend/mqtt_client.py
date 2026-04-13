import json
import logging
import base64
from datetime import datetime
import paho.mqtt.client as mqtt
from ai.detect import detect_human
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
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def start(self):
        logger.info(f"Connecting to MQTT broker {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEPALIVE)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"MQTT connected, subscribing to {MQTT_TOPIC_FILTER}")
            self.client.subscribe(MQTT_TOPIC_FILTER)
        else:
            logger.error(f"MQTT connection failed with rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        logger.warning(f"MQTT disconnected, rc={rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            data = json.loads(payload)
            device_id = data.get('device_id')
            timestamp_str = data.get('timestamp')
            image_b64 = data.get('image')

            if not device_id or not timestamp_str or not image_b64:
                logger.warning("MQTT message missing required fields")
                return

            timestamp = datetime.fromisoformat(timestamp_str)
            image_bytes = base64.b64decode(image_b64)

            if SAVE_IMAGES:
                self._save_local_image(device_id, image_bytes, timestamp)

            logger.info(f"Received motion event from {device_id}, running human detection")
            human_detected, confidence = detect_human(image_bytes)

            if human_detected:
                alert = self.coordinator.add_detection(device_id, timestamp, confidence)
                if alert:
                    send_alert(device_id, image_bytes, alert['message'])
            else:
                logger.info(f"No human detected for {device_id}")

        except Exception as exc:
            logger.error(f"Failed to handle MQTT message: {exc}")

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
