import logging
from datetime import datetime, timedelta
from collections import deque
from config import DETECTION_WINDOW_SECONDS, ALERT_COOLDOWN_SECONDS, DETECTION_HISTORY_SIZE

logger = logging.getLogger(__name__)

class MultiCameraCoordinator:
    def __init__(self):
        self.events = {}  # {device_id: {'timestamp': datetime, 'confidence': float}}
        self.history = deque(maxlen=DETECTION_HISTORY_SIZE)
        self.last_alert_time = datetime.min.replace(tzinfo=None)  # offset-naive
        self.last_alert_signature = None

    def add_detection(self, device_id, timestamp, confidence):
        """Add a new detection event and decide whether to send an alert."""
        self.events[device_id] = {
            'timestamp': timestamp,
            'confidence': confidence
        }
        self.history.append({
            'device_id': device_id,
            'timestamp': timestamp,
            'confidence': confidence
        })

        self._cleanup_old_events(timestamp)

        event = self._build_event(timestamp)
        if event and self._should_send_alert(event['signature'], timestamp):
            self.last_alert_time = timestamp
            self.last_alert_signature = event['signature']
            return event
        return None

    def _cleanup_old_events(self, current_time):
        cutoff = current_time - timedelta(seconds=DETECTION_WINDOW_SECONDS)
        stale_devices = [device for device, data in self.events.items() if data['timestamp'] < cutoff]
        for device in stale_devices:
            del self.events[device]

    def _build_event(self, current_time):
        active_devices = [device for device, data in self.events.items()]

        if len(active_devices) >= 2:
            sorted_devices = sorted(active_devices)
            signature = f"multi:{','.join(sorted_devices)}"
            message = (
                f"🚨 MULTI-CAMERA ALERT: Human detected by {sorted_devices[0]} "
                f"and {sorted_devices[1]}"
            )
            logger.info(f"Multi-camera event built: {message}")
            return {
                'type': 'multi',
                'message': message,
                'devices': sorted_devices,
                'signature': signature
            }

        if len(active_devices) == 1:
            device_id = active_devices[0]
            signature = f"single:{device_id}"
            message = f"⚠️ Human detected at Camera {device_id}"
            logger.info(f"Single-camera event built: {message}")
            return {
                'type': 'single',
                'message': message,
                'devices': [device_id],
                'signature': signature
            }

        return None

    def _should_send_alert(self, signature, current_time):
        # Ensure both datetimes are offset-naive to avoid comparison errors
        if hasattr(current_time, 'tzinfo') and current_time.tzinfo is not None:
            current_time = current_time.replace(tzinfo=None)
        if hasattr(self.last_alert_time, 'tzinfo') and self.last_alert_time.tzinfo is not None:
            self.last_alert_time = self.last_alert_time.replace(tzinfo=None)
            
        if self.last_alert_signature == signature and (
            (current_time - self.last_alert_time).total_seconds() < ALERT_COOLDOWN_SECONDS
        ):
            logger.debug("Skipping duplicate alert within cooldown window")
            return False

        if (current_time - self.last_alert_time).total_seconds() < ALERT_COOLDOWN_SECONDS:
            logger.debug("Skipping alert because cooldown is active")
            return False

        return True

    def get_history(self):
        return list(self.history)
