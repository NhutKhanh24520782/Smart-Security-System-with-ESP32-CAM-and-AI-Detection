# Smart Security System with ESP32-CAM and AI Detection

A complete IoT security system using ESP32-CAM modules with PIR sensors, AI-powered human detection, and Telegram notifications.

## 🏗️ Architecture

```
[PIR Sensor] → [ESP32-CAM] → MQTT Publish → [Flask Backend MQTT Subscriber]
                                      ↓
                               [AI Detection (OpenCV/AWS)]
                                      ↓
                               [Multi-Camera Coordinator]
                                      ↓
                               [Telegram Bot Alert]
```

## 📁 Project Structure

```
project/
├── esp32/
│   ├── cam1/
│   │   └── main.ino          # ESP32 MQTT publisher for Camera 1
│   └── cam2/
│       └── main.ino          # ESP32 MQTT publisher for Camera 2
├── backend/
│   ├── app.py                # Flask server + MQTT subscriber launcher
│   ├── mqtt_client.py        # MQTT client subscribing to camera events
│   ├── config.py             # Configuration settings
│   ├── register_face.py      # Register new faces
│   ├── setup_aws.py          # Establish AWS Rekognition connection
│   ├── ai/
│   │   └── detect.py         # AI human detection module
│   ├── coordination/
│   │   └── coordinator.py    # Multi-camera alert coordination logic
│   └── services/
│       └── telegram.py       # Telegram notification service
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🔧 Hardware Requirements

- 2 x ESP32-CAM modules
- 2 x PIR motion sensors
- 2 x Active buzzers (LOW trigger)
- WiFi network
- Power supplies for ESP32-CAM

## 🚀 Setup Instructions

### 1. Backend Setup

#### Install Dependencies
```bash
cd backend
pip install -r ../requirements.txt
```

#### Configure Settings
Edit `backend/config.py`:

```python
# MQTT broker configuration
MQTT_BROKER_HOST = 'YOUR_MQTT_BROKER_HOST'
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = 'YOUR_MQTT_USERNAME'
MQTT_PASSWORD = 'YOUR_MQTT_PASSWORD'
MQTT_TOPIC_FILTER = 'camera/+/motion'

# Telegram Bot
TELEGRAM_BOT_TOKEN = 'your_bot_token_from_botfather'
TELEGRAM_CHAT_ID = 'your_chat_id'

# AI Method
AI_METHOD = 'opencv'  # or 'aws'

# AWS (if using AWS Rekognition)
AWS_ACCESS_KEY = 'your_access_key'
AWS_SECRET_KEY = 'your_secret_key'
```

#### Get Telegram Bot Token
1. Message @BotFather on Telegram
2. Create new bot: `/newbot`
3. Follow instructions to get token
4. Start chat with your bot
5. Send a message to get chat_id (use a tool or manually)

#### Run Backend Server
```bash
cd backend
# Activate virtual environment
source ../venv/bin/activate  # On Windows: ../venv/Scripts/activate
python app.py
```

Server will run on `http://localhost:5000`

### 2. ESP32 Setup

#### Hardware Connections
- PIR Sensor OUT → GPIO 13
- Buzzer → GPIO 12 (LOW active)
- Camera module: Standard ESP32-CAM pinout

#### Flash ESP32
1. Install Arduino IDE
2. Install ESP32 board support
3. Install required libraries:
   - WiFi
   - PubSubClient
   - ESP32 Camera
4. Open `esp32/cam1/main.ino` or `esp32/cam2/main.ino`
5. Update WiFi credentials and backend IP
6. Select board: ESP32 Wrover Module
7. Upload code

#### ESP32 Configuration
Update in each `main.ino`:

#### Face detect Configuration
1. Add your acquaintance face in backend folder
2. Edit register_face.py
3. Run register_face.py: pthyon register_face.py

```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqttBroker = "YOUR_MQTT_BROKER_HOST";
const int mqttPort = 1883;
const char* mqttUser = "YOUR_MQTT_USERNAME";
const char* mqttPassword = "YOUR_MQTT_PASSWORD";
```

## 🧪 Testing

### Test Backend
```bash
# Activate virtual environment first
source venv/bin/activate

# Health check
curl http://localhost:5000/health
```

The MQTT flow is validated by connecting ESP32 devices to your broker and confirming that the backend receives messages on `camera/+/motion`.

If you want to keep the HTTP fallback endpoint, test it with:
```bash
curl -X POST -F "device_id=cam1" -F "image=@test_image.jpg" http://localhost:5000/upload
```

### Test ESP32
1. Power on ESP32
2. Check serial monitor for connection logs
3. Trigger PIR sensor
4. Verify buzzer activates and image is sent

### Test Full System
1. Start backend server
2. Flash and power ESP32
3. Trigger motion detection
4. Check Telegram for alerts

## 🔍 AI Detection Options

### OpenCV (Default)
- Uses HOG descriptor for human detection
- No external dependencies
- Works offline

### AWS Rekognition
- More accurate detection
- Requires AWS account and API costs
- Set `AI_METHOD = 'aws'` in config

## 📊 Features

- ✅ Motion detection with debounce
- ✅ Cooldown period between triggers
- ✅ Image capture and transmission
- ✅ AI-powered human detection
- ✅ Acquaintances or strangers detection
- ✅ Telegram alerts with images
- ✅ Multi-device support
- ✅ Local image logging
- ✅ Confidence thresholding
- ✅ Comprehensive logging

## 🔧 Configuration Options

### Timing
- Debounce delay: 2 seconds
- Cooldown period: 15 seconds
- Buzzer duration: 1 second

### Camera
- Resolution: 640x480 (VGA)
- JPEG quality: 12 (higher quality)

### Detection
- Confidence threshold: 0.5 (50%)

## 🐛 Troubleshooting

### ESP32 Issues
- Check WiFi credentials
- Verify camera connections
- Monitor serial output

### Backend Issues
- Check Flask logs
- Verify Telegram token/chat_id
- Test AI detection separately

### Network Issues
- Ensure ESP32 and backend on same network
- Check firewall settings
- Verify IP addresses

## 📈 Future Enhancements

- Web dashboard for monitoring
- Multiple AI models
- Video streaming
- Mobile app notifications
- Cloud storage integration
- Advanced analytics

## 📄 License

This project is open source. Feel free to modify and distribute.

---

Built with ❤️ for IoT security applications