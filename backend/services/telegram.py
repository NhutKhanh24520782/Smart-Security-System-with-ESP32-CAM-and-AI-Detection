import requests
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_alert(self, device_id, image_bytes=None, message=None):
        """
        Send alert message to Telegram with optional image

        Args:
            device_id: Camera device identifier (cam1, cam2)
            image_bytes: Raw image bytes (optional)
            message: Optional caption message
        """
        try:
            if not message:
                message = f"⚠️ Human detected at {device_id.upper()}"

            if image_bytes:
                # Send photo with caption
                self._send_photo(message, image_bytes)
            else:
                # Send text message only
                self._send_message(message)

            logger.info(f"Alert sent to Telegram for {device_id}")

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {str(e)}")

    def _send_message(self, message):
        """Send text message to Telegram"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

    def _send_photo(self, caption, image_bytes):
        """Send photo with caption to Telegram"""
        url = f"{self.base_url}/sendPhoto"
        files = {
            'photo': ('capture.jpg', image_bytes, 'image/jpeg')
        }
        data = {
            'chat_id': self.chat_id,
            'caption': caption
        }

        response = requests.post(url, files=files, data=data, timeout=10)
        response.raise_for_status()

# Global service instance
telegram_service = TelegramService()

def send_alert(device_id, image_bytes=None, message=None):
    """
    Convenience function to send alert

    Args:
        device_id: Camera device identifier
        image_bytes: Raw image bytes (optional)
        message: Optional custom caption message
    """
    telegram_service.send_alert(device_id, image_bytes, message)