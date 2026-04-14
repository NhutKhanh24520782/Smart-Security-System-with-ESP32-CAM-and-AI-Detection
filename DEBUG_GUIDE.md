# 🔍 Camera Debug Guide

## Current Setup
- **Backend**: Flask on port 5000 (10.87.175.110)
- **ESP32 cam1**: Port 80 (10.87.175.144)
- **MQTT Broker**: HiveMQ Cloud port 8883

## Debugging Steps

### 1. **Check Camera Initialization**
Upload the latest code to ESP32 and check serial monitor for:
```
🎥 Initializing camera...
✅ Camera initialized successfully
✅ First frame captured: XXXX bytes
```

❌ **If you see errors**, the camera isn't being recognized:
- Verify GPIO pins match your ESP32-CAM variant (PWDN_GPIO_NUM 32, etc.)
- Check camera ribbon cable is fully inserted
- Ensure adequate power supply (ESP32-CAM needs 5V, min 500mA)
- Try longer delay: Add `delay(1000)` after `initCamera()` in setup()

---

### 2. **Test Camera HTTP Endpoint Manually**
Without waiting for motion detection, test if camera captures:

```bash
# Option A: From Linux terminal
curl -i http://10.87.175.144:80/capture -o test_image.jpg

# Option B: Check if /test endpoint works
curl -i http://10.87.175.144:80/test -o test_image2.jpg

# Option C: Check health status
curl http://10.87.175.144:80/health
```

**Expected response**:
- HTTP 200 with JPEG binary data (>100 bytes)
- ESP32 serial: `📸 handleCapture() called` + `✅ Frame captured: XXXX bytes`

❌ **If you get 500 error or empty response**:
- `esp_camera_fb_get() returned NULL` = Frame buffer not initialized
- Check serial logs for camera init errors

---

### 3. **Monitor ESP32 Serial Output**
Watch for the complete flow:

```
1. WiFi connected: 10.87.175.144          ✅ Part A: Network
2. MQTT connected to broker                ✅ Part B: MQTT auth
3. HTTP server started on port 80          ✅ Part C: HTTP server
4. 📍 PIR triggered                        ✅ Part D: Motion detection
5. 🔴 Motion detected!                     ✅ Part E: Debounce
6. 📤 Publishing MQTT payload              ✅ Part F: MQTT publish
   {"device_id":"cam1",...,"ip":"..."}
7. ✅ Motion event published               ✅ Part G: Publish success
```

**Troubleshooting each part**:

| Part | Issue | Solution |
|------|-------|----------|
| A | WiFi not connecting | Check SSID/password in code |
| B | MQTT rc=-2 | Check broker host/port/credentials |
| C | HTTP server fails | Check WebServer library installed |
| D | No PIR trigger | Test PIR sensor separately (should go HIGH on motion) |
| E | ⏳ Cooldown messages | Wait 15s, motion detection has cooldown |
| F | No payload logging | Check MQTT buffer size (32KB set) |
| G | ❌ Publish failed (rc=-4) | MQTT not connected, check part B |

---

### 4. **Backend Should Try to Fetch Image**
After ESP32 publishes MQTT event, backend logs should show:

```
📨 MQTT message received from topic 'camera/cam1/motion'
🔴 Motion event from cam1
   Device IP: 10.87.175.144
🔴 Fetching image via HTTP from cam1...
   🔗 HTTP GET http://10.87.175.144:80/capture (attempt 1/3)...
   ✅ Image fetched: XXXX bytes
🧠 Running AI detection on image from cam1
✅ Human detected by cam1 (confidence=0.XX)
🚨 Sending alert: ...
```

❌ **If you DON'T see "Fetching image" message**:
- Backend might not be receiving MQTT message
- Check MQTT topic matches: `camera/+/motion` filter should catch `camera/cam1/motion`
- Verify both backend and ESP32 connected to same MQTT broker

---

### 5. **Test MQTT Connection Independently**
Use a MQTT client to verify:

```bash
# Install MQTT client
sudo apt install mosquitto-clients

# Subscribe to topic
mosquitto_sub -h 47aba3e9f3f94aa8b2f163688423010c.s1.eu.hivemq.cloud \
  -p 8883 \
  -u backend \
  -P Nhutkhanh2025 \
  --cafile /etc/ssl/certs/ca-certificates.crt \
  -t "camera/+/motion"

# Trigger motion on ESP32, check if message appears
```

---

## Common Camera Issues & Fixes

### 🔴 Issue: Camera init failed with error 0x5
- **Cause**: INVALID_ARG (incorrect GPIO pins)
- **Fix**: Verify GPIO defines match your ESP32-CAM pinout

### 🔴 Issue: Camera init failed with error 0x2  
- **Cause**: INVALID_STATE (camera already initialized)
- **Fix**: Only call `initCamera()` once in `setup()`

### 🔴 Issue: Camera init failed with error 0x1
- **Cause**: NO_MEM (insufficient PSRAM/memory)
- **Fix**: Reduce JPEG quality (lower than 12), or use smaller frame size

### 🔴 Issue: Frame buffer size is 0
- **Cause**: Camera not capturing valid data
- **Fix**: Add delay after camera init, check power supply

### 🔴 Issue: HTTP 500 every time, but init says success
- **Cause**: `esp_camera_fb_get()` only fails after a while
- **Fix**: Check if there's PSRAM allocation issue or infinite loop

---

## PIN Configuration Reference

**Standard ESP32-CAM Pinout** (verify against your board):
```
PWDN_GPIO_NUM     = 32   (Power Down)
RESET_GPIO_NUM    = -1   (No reset pin)
XCLK_GPIO_NUM     = 0    (Clock)
SIOD_GPIO_NUM     = 26   (SDA I2C)
SIOC_GPIO_NUM     = 27   (SCL I2C)
Sensor pins       = 35,34,39,36,21,19,18,5 (D0-D7)
VSYNC/HREF/PCLK   = 25,23,22
PIR_PIN           = 13   (GPIO13)
BUZZER_PIN        = 14   (GPIO14)
```

If using **different ESP32 variant**, verify pinout!

---

## Next Steps After Debug

1. ✅ Verify ESP32 can capture frames locally (`/test` endpoint)
2. ✅ Verify curl from Linux can fetch images  
3. ✅ Monitor ESP32 logs show complete flow
4. ✅ Monitor backend logs show MQTT message + HTTP fetch
5. ✅ Check `/captured_images/` folder for saved images
6. ✅ Verify Telegram alerts are received

