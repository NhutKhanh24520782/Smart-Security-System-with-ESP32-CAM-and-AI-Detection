# Door Control Implementation - Người Quen Mở Cửa Tự Động

## Tóm tắt
Hệ thống giờ đây có thể gửi tín hiệu mở cửa tự động khi phát hiện được một **người quen** (KNOWN person) qua camera ESP32-CAM.

## Các Thay Đổi Được Thực Hiện

### 1. Backend - `backend/mqtt_client.py`
**Thêm 2 tính năng chính:**

#### A. Phương thức mới: `_send_door_open_command()`
- Gửi MQTT message đến topic `door/cam1/control`
- Payload JSON:
```json
{
  "command": "open",
  "action": "UNLOCK_DOOR",
  "detected_persons": ["Tên người quen"],
  "timestamp": "2026-05-18T..."
}
```
- Sử dụng QoS level 1 để đảm bảo độ tin cậy

#### B. Sửa đổi `_on_message()` method
- Kiểm tra danh sách `detection_result['faces']` có chứa face nào có `status == 'KNOWN'` không
- Nếu có, gọi `_send_door_open_command()` để gửi lệnh mở cửa

**Code:**
```python
# Check if any known person detected and send door open command
known_faces = [face for face in detection_result.get('faces', []) 
              if face.get('status') == 'KNOWN']
if known_faces:
    logger.info(f"🔓 Known person(s) detected: {[f.get('name') for f in known_faces]}")
    self._send_door_open_command(device_id, known_faces)
```

### 2. Backend - `backend/app.py`
**Sửa đổi endpoint `/upload`:**
- Thêm logic kiểm tra KNOWN faces
- Gọi `mqtt_client_instance._send_door_open_command()` khi có người quen
- Tương tự như MQTT client, đảm bảo cả HTTP upload cũng kích hoạt mở cửa

### 3. ESP32 - `esp32/cam1/main/main.ino`
**Thêm 2 sửa đổi chính:**

#### A. Thêm ArduinoJson library
```cpp
#include <ArduinoJson.h>  // ✅ JSON parsing library
```

#### B. Sửa đổi `onMqttMessage()` callback
- Parse JSON payload từ backend
- Hỗ trợ cả định dạng JSON và simple string (backward compatible)
- Khi nhận `command: "open"` hoặc `action: "UNLOCK_DOOR"`, gọi `openDoor()`

**Cách hoạt động:**
```
1. Backend phát hiện người quen từ AI recognition
2. Backend gửi MQTT message tới topic: door/cam1/control
3. ESP32 nhận message và parse JSON
4. Servo được điều khiển để mở cửa (góc 120°)
5. Buzzer phát âm thanh xác nhận
6. Cửa tự động đóng sau 3 giây
```

## Flow Hoạt Động

### Scenario: Người Quen Đến (via MQTT Motion)
```
1. PIR sensor phát hiện chuyển động → gửi MQTT motion event
2. Backend nhận MQTT event → lấy ảnh qua HTTP
3. Backend chạy AI face recognition (AWS Rekognition)
4. Kết quả: KNOWN person detected
5. Backend gửi MQTT: door/cam1/control → {"command": "open", ...}
6. ESP32 nhận MQTT → openDoor() → Servo mở
7. Buzzer phát âm thanh
8. Cửa tự động đóng sau 3 giây
```

### Scenario: Người Lạ Đến (via MQTT Motion)
```
1. PIR sensor phát hiện → MQTT motion event
2. Backend: UNKNOWN person detected
3. Backend gửi Telegram alert nhưng KHÔNG gửi lệnh mở cửa
4. Cửa vẫn đóng
```

## Configuration
- **Servo Open Duration:** 3 giây (có thể sửa `SERVO_OPEN_DURATION` trong main.ino)
- **Servo Open Angle:** 120° (có thể sửa `SERVO_OPEN_ANGLE`)
- **Servo Closed Angle:** 0° (có thể sửa `SERVO_CLOSED_ANGLE`)
- **Door Control Topic:** `door/cam1/control`
- **QoS Level:** 1 (ít nhất một lần gửi)

## Dependencies
### ESP32
- ArduinoJson (v6.x trở lên) - cần cài đặt qua Arduino IDE Library Manager

### Backend
- paho-mqtt (đã có)
- Requests (đã có)
- Flask (đã có)

## Kiểm Tra Hoạt Động

### 1. Xem logs backend:
```bash
tail -f logs/backend.log | grep -E "🔓|Known person|door open"
```

### 2. Xem logs ESP32:
Mở Serial Monitor (9600 baud), tìm message như:
```
📨 MQTT Message received on topic: door/cam1/control
✅ JSON payload parsed successfully
🔓 Backend command: OPEN DOOR (known person detected)
🚪 Opening door...
✅ Door opened, servo at 120°
```

### 3. Test manual (qua MQTT):
```bash
mosquitto_pub -h <MQTT_HOST> -u <USER> -P <PASSWORD> \
  -t door/cam1/control \
  -m '{"command":"open","action":"UNLOCK_DOOR","detected_persons":["Test"]}'
```

## Lưu Ý Quan Trọng
- ✅ System sẽ CHỈ mở cửa khi phát hiện **KNOWN person**
- ✅ Cửa tự động đóng sau 3 giây
- ✅ Buzzer phát âm thanh để xác nhận hành động
- ✅ Hỗ trợ cả MQTT motion và HTTP upload từ app.py
- ⚠️  Ensure ArduinoJson library được cài trên Arduino IDE

## Troubleshooting

### Cửa không mở
1. Kiểm tra servo có pin 12 không
2. Kiểm tra MQTT connection (Serial log)
3. Kiểm tra JSON parsing (search "JSON parsing" trong Serial output)
4. Test manual qua mosquitto_pub

### Backend không gửi lệnh
1. Kiểm tra face recognition kết quả (log của detect.py)
2. Kiểm tra mqtt_client_instance initialize đúng không
3. Xem logs: search "🔓 Known person"

### ArduinoJson parse error
1. Cài đặt: Sketch → Include Library → Manage Libraries → ArduinoJson
2. Chọn version 6.x (khuyên dùng 6.20+)
3. Recompile và upload

## Future Enhancements
- [ ] Thêm face recognition cho cam2 với servo riêng
- [ ] Thêm database lưu lại lịch sử mở cửa
- [ ] Thêm 2FA (two-factor authentication) cho extra security
- [ ] Thêm time-based auto-unlock (mở cửa trong giờ làm việc)
