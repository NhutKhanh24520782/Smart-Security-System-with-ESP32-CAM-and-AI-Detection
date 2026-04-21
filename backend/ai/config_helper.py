"""
AWS Rekognition Configuration Helper

This shows the complete configuration needed for the face detection system.
Copy/reference these settings in your backend/config.py
"""

# ============================================================================
# AWS REKOGNITION CONFIGURATION
# ============================================================================

# Your AWS Region (where Rekognition is available)
AWS_REGION = 'us-east-1'  # Options: us-east-1, us-west-2, eu-west-1, etc.

# AWS Credentials (obtain from AWS IAM Console)
# ⚠️  NEVER commit these to public repositories!
AWS_ACCESS_KEY = 'your-aws-access-key-id'
AWS_SECRET_KEY = 'your-aws-secret-access-key'

# ============================================================================
# REKOGNITION COLLECTION SETTINGS
# ============================================================================

# Name of your Rekognition face collection
# This is created automatically on first use
AWS_FACE_COLLECTION_ID = 'smart-security-collection'

# Face matching confidence threshold (0-100)
# Lower values = stricter matching (fewer false positives but might miss matches)
# Higher values = lenient matching (might have more false positives)
# Recommended: 80-90 for security applications
AWS_FACE_MATCH_THRESHOLD = 80.0

# Face similarity threshold for search_faces_by_image (0-100)
# Controls how similar a detected face must be to match against collection
# Recommended: 80 (adjustable based on your accuracy needs)
AWS_FACE_SIMILARITY_THRESHOLD = 80.0

# ============================================================================
# LOCAL STORAGE SETTINGS
# ============================================================================

# File to store known faces database (maps FaceId -> Name)
# Maps AWS FaceIds to readable person names
# Format: JSON {"face-id": {"name": "John Doe", "registered_at": "...", ...}}
AWS_KNOWN_FACES_DB = 'known_faces.json'

# Directory to save unknown/unrecognized faces
# Automatically created on first use
# Useful for later review and potential registration
AWS_UNKNOWN_FACES_DIR = 'unknown_faces/'

# ============================================================================
# ADDITIONAL OPTIONS (Optional Customization)
# ============================================================================

# Delete unknown face images after N days (optional)
# Leave as False to keep indefinitely
UNKNOWN_FACES_RETENTION_DAYS = False  # or set to: 7, 30, etc.

# Minimum image quality for face registration
# 'LOW', 'MEDIUM', 'HIGH', 'AUTO'
AWS_FACE_QUALITY_FILTER = 'AUTO'

# Maximum faces to detect per image
AWS_MAX_FACES_PER_IMAGE = 10

# Store face embeddings locally for offline comparison (advanced)
AWS_STORE_EMBEDDINGS = False

# ============================================================================
# COMPLETE CONFIG.PY SETTINGS
# ============================================================================

COMPLETE_CONFIG = """
# ========== Flask Configuration ==========
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5002
FLASK_DEBUG = False

# ========== Telegram Configuration ==========
TELEGRAM_BOT_TOKEN = '8798378490:AAE7timUHd8ZPFWybJox6ODXtNgEs0blrjQ'
TELEGRAM_CHAT_ID = '5441757076'

# ========== AI Detection Configuration ==========
AI_METHOD = 'aws'  # Options: 'opencv', 'aws'
CONFIDENCE_THRESHOLD = 0.5

# ========== AWS Rekognition Configuration ==========
AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY = 'your-access-key'
AWS_SECRET_KEY = 'your-secret-key'

# AWS Rekognition Face Recognition settings
AWS_FACE_COLLECTION_ID = 'smart-security-collection'
AWS_FACE_MATCH_THRESHOLD = 80.0
AWS_FACE_SIMILARITY_THRESHOLD = 80.0
AWS_KNOWN_FACES_DB = 'known_faces.json'
AWS_UNKNOWN_FACES_DIR = 'unknown_faces/'

# ========== MQTT Configuration ==========
MQTT_BROKER_HOST = '47aba3e9f3f94aa8b2f163688423010c.s1.eu.hivemq.cloud'
MQTT_BROKER_PORT = 8883
MQTT_USERNAME = 'backend'
MQTT_PASSWORD = 'Nhutkhanh2025'
MQTT_TOPIC_FILTER = 'camera/+/motion'
MQTT_KEEPALIVE = 60
MQTT_DEBUG = False

# ========== Multi-Camera Coordination ==========
DETECTION_WINDOW_SECONDS = 5
ALERT_COOLDOWN_SECONDS = 30
DETECTION_HISTORY_SIZE = 50

# ========== Logging Configuration ==========
LOG_LEVEL = 'INFO'
LOG_FILE = 'security_system.log'

# ========== Image Storage ==========
IMAGE_SAVE_PATH = 'captured_images/'
SAVE_IMAGES = True
"""

# ============================================================================
# STEP-BY-STEP SETUP GUIDE
# ============================================================================

SETUP_GUIDE = """
1. OBTAIN AWS CREDENTIALS
   - Go to AWS IAM Console (https://console.aws.amazon.com/iam/)
   - Create a new IAM user with Rekognition permissions
   - Generate Access Key ID and Secret Access Key
   - Download credentials.csv and keep safe!

2. ENABLE AWS REKOGNITION
   - Go to AWS Rekognition Console
   - Ensure service is enabled in your region (us-east-1, etc.)

3. UPDATE CONFIG.PY
   - Open backend/config.py
   - Replace AWS_ACCESS_KEY with your Access Key ID
   - Replace AWS_SECRET_KEY with your Secret Access Key
   - Set AWS_REGION to your preferred region

4. INSTALL DEPENDENCIES
   - pip install boto3

5. INITIALIZE SYSTEM (One-Time)
   - from ai.detect import init_detector
   - detector = init_detector()
   - detector.create_collection()

6. REGISTER KNOWN PERSONS
   - from ai.detect import register_face
   - with open('john.jpg', 'rb') as f:
   -     register_face(f.read(), 'John Doe')

7. INTEGRATE WITH FLASK
   - See example_usage.py for Flask integration
   - Add detection endpoint to app.py

8. TEST
   - Send image to Flask endpoint
   - Check Telegram for alerts
   - Review unknown_faces/ directory
"""

# ============================================================================
# THRESHOLD TUNING GUIDE
# ============================================================================

THRESHOLD_GUIDE = """
AWS_FACE_MATCH_THRESHOLD (Confidence for matches):

  Conservative (Strict): 90-95
  - Few false positives
  - Might miss some matches
  - Best for high-security applications
  
  Balanced (Recommended): 80-85
  - Good balance of precision and recall
  - Standard security use
  - Good for home/office security
  
  Liberal (Lenient): 70-75
  - More matches found
  - More false positives possible
  - Use only if you need high recall

How to find optimal value:
1. Start with 80 (recommended)
2. Test with your known faces
3. If too many false positives → increase to 85-90
4. If missing known faces → decrease to 70-75
5. Fine-tune based on your results
"""

# ============================================================================
# TROUBLESHOOTING CHECKLIST
# ============================================================================

TROUBLESHOOTING = """
Problem: "InvalidParameterException" when detecting faces
Solution: 
  - Check AWS credentials are correct
  - Verify AWS_REGION is correct
  - Ensure Rekognition service is enabled in that region

Problem: "Collection not found" error
Solution:
  - Run: detector.create_collection() to create it
  - Check collection name in AWS_FACE_COLLECTION_ID

Problem: Known faces not being recognized
Solution:
  - Verify faces are registered: list_known_faces()
  - Check confidence threshold isn't too high
  - Ensure good image quality (lighting, face size)
  - Try lowering AWS_FACE_SIMILARITY_THRESHOLD

Problem: Too many false positives
Solution:
  - Increase AWS_FACE_MATCH_THRESHOLD (e.g., 85-90)
  - Ensure registered faces are high quality
  - Re-register faces with better photos

Problem: Unknown faces not saving
Solution:
  - Check unknown_faces/ directory exists
  - Verify directory permissions (writable)
  - Check disk space available

Problem: Telegram alerts not arriving
Solution:
  - Verify TELEGRAM_BOT_TOKEN is correct
  - Check TELEGRAM_CHAT_ID is correct
  - Test bot can send messages
  - Check bot permissions in chat/group
"""

# ============================================================================
# PRICING ESTIMATE (as of 2024)
# ============================================================================

PRICING_INFO = """
AWS Rekognition Pricing (approximate):

detect_faces():
  - $0.0015 per image (1000 images = $1.50)
  - Free tier: 5,000 images/month

search_faces_by_image():
  - $0.0015 per image
  - Free tier: 1,000 searches/month (not included in API tier)

index_faces():
  - $0.001 per image
  - Free tier: 1,000 faces/month

Estimated Monthly Cost for Home Security:
  - 100 detections/day = 3,000/month = ~$4.50
  - 50 searches/day = 1,500/month = ~$2.25
  - 10 registrations/month = ~$0.01
  Total: ~$7/month

Note: Prices vary by region. Check AWS pricing page for current rates.
Free tier provides significant allowance - good for home use!
"""

if __name__ == '__main__':
    print("=" * 70)
    print("AWS REKOGNITION CONFIGURATION HELPER")
    print("=" * 70)
    print("\n" + COMPLETE_CONFIG)
    print("\n" + "=" * 70)
    print("SETUP GUIDE")
    print("=" * 70)
    print(SETUP_GUIDE)
    print("\n" + "=" * 70)
    print("THRESHOLD TUNING")
    print("=" * 70)
    print(THRESHOLD_GUIDE)
