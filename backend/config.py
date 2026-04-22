# Configuration file for the smart security system backend

# Flask server configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5002
FLASK_DEBUG = False  # Disable debug mode to prevent restart loop from log/image writes

# Telegram bot configuration
TELEGRAM_BOT_TOKEN = '8798378490:AAE7timUHd8ZPFWybJox6ODXtNgEs0blrjQ'  # Get from @BotFather
TELEGRAM_CHAT_ID = '6937833381'      # Get chat ID from bot

# AI Detection configuration
AI_METHOD = 'aws'  # Options: 'opencv', 'aws'
CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for detection

# AWS Rekognition (if using AWS)
AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY = 'AKIAXCRJJAXMZ7X5F7OU'  # Replace with real key
AWS_SECRET_KEY = 'Wiw2IHXSGEb4lh9fHuGIBsoQbMersOp5c4emfCc5'  # Replace with real secret

# AWS Rekognition Face Recognition settings
AWS_FACE_COLLECTION_ID = 'smart-security-collection'  # Rekognition collection for known faces
AWS_FACE_MATCH_THRESHOLD = 80.0  # Confidence threshold for face matching (0-100)
AWS_FACE_SIMILARITY_THRESHOLD = 80.0  # Similarity threshold for search_faces_by_image (0-100)
AWS_KNOWN_FACES_DB = 'known_faces.json'  # Local JSON file for faceId <-> name mapping
AWS_UNKNOWN_FACES_DIR = 'unknown_faces/'  # Directory to save unknown faces for review

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
