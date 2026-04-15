# Configuration file for the smart security system backend

# Flask server configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5002
FLASK_DEBUG = False  # Disable debug mode to prevent restart loop from log/image writes

# Telegram bot configuration
TELEGRAM_BOT_TOKEN = '8798378490:AAE7timUHd8ZPFWybJox6ODXtNgEs0blrjQ'  # Get from @BotFather
TELEGRAM_CHAT_ID = '5441757076'      # Get chat ID from bot

# AI Detection configuration
AI_METHOD = 'aws'  # Options: 'opencv', 'aws'
CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for detection

# AWS Rekognition (if using AWS)
AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY = 'AKIAXCRJJAXM77V7ZAMA'
AWS_SECRET_KEY = '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'

# MQTT broker configuration
MQTT_BROKER_HOST = '47aba3e9f3f94aa8b2f163688423010c.s1.eu.hivemq.cloud'
MQTT_BROKER_PORT = 8883
MQTT_USERNAME = 'backend'
MQTT_PASSWORD = 'Nhutkhanh2025'
MQTT_TOPIC_FILTER = 'camera/+/motion'
MQTT_KEEPALIVE = 60
MQTT_DEBUG = False

# Multi-camera coordination
DETECTION_WINDOW_SECONDS = 5
ALERT_COOLDOWN_SECONDS = 30
DETECTION_HISTORY_SIZE = 50

# Logging configuration
LOG_LEVEL = 'INFO'
LOG_FILE = 'security_system.log'

# Image storage
IMAGE_SAVE_PATH = 'captured_images/'  # Directory to save captured images
SAVE_IMAGES = True  # Whether to save images locally
