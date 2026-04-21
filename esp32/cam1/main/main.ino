#define MQTT_MAX_PACKET_SIZE 262144
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <WebServer.h>  // ✅ HTTP server cho gửi ảnh
#include <esp_camera.h>
#include <time.h>

// Pin definitions
#define PIR_PIN 13        // PIR sensor pin
#define BUZZER_PIN 14     // Buzzer pin (LOW active)
#define FLASH_LED_PIN 4   // LED Flash pin (HIGH to turn on)

// Camera pins for ESP32-CAM
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// WiFi credentials
const char* ssid = "khoaaaa";
const char* password = "dangkihocphan";

// MQTT config
const char* mqttBroker = "47aba3e9f3f94aa8b2f163688423010c.s1.eu.hivemq.cloud";
const int mqttPort = 8883;
const char* mqttUser = "esp32cam1";
const char* mqttPassword = "Nhutkhanh2025";
const char* deviceId = "cam1";
String mqttTopic = String("camera/") + deviceId + "/motion";

// Timing variables
unsigned long lastTriggerTime = 0;
const unsigned long cooldownPeriod = 15000; // 15 seconds cooldown
const unsigned long debounceDelay = 2000;   // 2 seconds debounce
unsigned long pirHighStart = 0;
bool pirStable = false;

// 🔍 PIR debug variables
unsigned long lastPirDebugTime = 0;
const unsigned long pirDebugInterval = 5000;  // Log PIR state every 5 sec
int lastPirState = -1;  // Track last state for change detection

WiFiClientSecure wifiClient;
PubSubClient mqttClient(wifiClient);
WebServer server(80);  // ✅ HTTP server port 80

static const char base64Chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

String getTimestamp() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return String(millis());
  }

  char buffer[32];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return String(buffer);
}

// ✅ HTTP handler để backend lấy ảnh (with LED flash indicator)
void handleCapture() {
  Serial.println("📸 handleCapture() called");
  
  // ✅ Bật LED flash để báo hiệu
  digitalWrite(FLASH_LED_PIN, HIGH);
  delay(100);  // Flash sáng ngắn
  
  camera_fb_t *fb = esp_camera_fb_get();
  
  // Tắt LED flash
  digitalWrite(FLASH_LED_PIN, LOW);
  
  if (!fb) {
    Serial.println("❌ esp_camera_fb_get() returned NULL - frame buffer not available!");
    server.send(500, "text/plain", "Capture failed - no frame buffer");
    return;
  }

  if (fb->len == 0) {
    Serial.println("❌ Frame buffer size is 0 - invalid frame!");
    esp_camera_fb_return(fb);
    server.send(500, "text/plain", "Capture failed - empty frame");
    return;
  }

  Serial.printf("✅ Frame captured: %d bytes (LED flashed)\n", fb->len);
  server.send_P(200, "image/jpeg", (const char *)fb->buf, fb->len);
  Serial.printf("📸 Image sent: %d bytes\n", fb->len);
  esp_camera_fb_return(fb);
}

// ✅ HTTP health check
void handleHealth() {
  server.send(200, "application/json", "{\"status\":\"ok\",\"device\":\"" + String(deviceId) + "\"}");
}

void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;  // 320x240
  config.jpeg_quality = 12;  // ✅ Normal quality
  config.fb_count = 1;

  Serial.println("🎥 Initializing camera...");
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Camera init failed with error 0x%x\n", err);
    switch(err) {
      case ESP_ERR_INVALID_ARG: Serial.println("   Reason: INVALID_ARG"); break;
      case ESP_ERR_INVALID_STATE: Serial.println("   Reason: INVALID_STATE"); break;
      case ESP_ERR_NO_MEM: Serial.println("   Reason: NO_MEM (out of memory)"); break;
      default: Serial.println("   Reason: Unknown error");
    }
    return;
  }
  Serial.println("✅ Camera initialized successfully");
  
  // Try first capture
  delay(500);
  camera_fb_t *test_fb = esp_camera_fb_get();
  if (test_fb) {
    Serial.printf("✅ First frame captured: %d bytes\n", test_fb->len);
    esp_camera_fb_return(test_fb);
  } else {
    Serial.println("❌ Failed to capture first frame!");
  }
}

void initTime() {
  configTime(0, 0, "pool.ntp.org", "time.google.com");
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo, 5000)) {
    Serial.println("Failed to obtain time from NTP");
  }
}

void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

void connectMqtt() {
  mqttClient.setServer(mqttBroker, mqttPort);
  mqttClient.setKeepAlive(60);
  mqttClient.setBufferSize(32768);  // ✅ 32KB (đủ cho ~20KB payload)

  while (!mqttClient.connected()) {
    Serial.printf("Connecting to MQTT broker %s:%d...\n", mqttBroker, mqttPort);
    if (mqttClient.connect(deviceId, mqttUser, mqttPassword)) {
      Serial.println("MQTT connected");
    } else {
      Serial.printf("MQTT connection failed, rc=%d. Retrying in 2s\n", mqttClient.state());
      delay(2000);
    }
  }
}

// ✅ MQTT: chỉ gửi event (không gửi ảnh!)
void publishMotionEvent() {
  if (!mqttClient.connected()) {
    Serial.println("❌ MQTT not connected, reconnecting...");
    connectMqtt();
  }

  delay(100);
  mqttClient.loop();
  
  // ✅ Event payload + IP (dynamic)
  String payload = "{";
  payload += "\"device_id\":\"" + String(deviceId) + "\",";
  payload += "\"motion\":true,";
  payload += "\"timestamp\":\"" + getTimestamp() + "\",";
  payload += "\"ip\":\"" + WiFi.localIP().toString() + "\"";
  payload += "}";
  
  Serial.printf("📤 Publishing MQTT payload (%d bytes):\n", payload.length());
  Serial.println("   " + payload);
  
  bool published = mqttClient.publish(mqttTopic.c_str(), payload.c_str());
  if (published) {
    Serial.printf("✅ Motion event published successfully to topic: %s\n", mqttTopic.c_str());
  } else {
    Serial.printf("❌ MQTT publish failed (state=%d)\n", mqttClient.state());
  }
}

// ❌ XÓA buildPayload (không cần nữa)

void captureAndSend() {
  Serial.println("🔴 captureAndSend() called - motion event triggered");
  
  // Buzzer pulse
  digitalWrite(BUZZER_PIN, LOW);
  delay(500);
  digitalWrite(BUZZER_PIN, HIGH);
  Serial.println("   Buzzer pulsed");

  // Capture image
  Serial.println("   Capturing image...");
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Failed to capture frame");
    publishMotionEvent();  // Fallback: publish MQTT only
    return;
  }
  Serial.printf("   ✅ Image captured: %d bytes\n", fb->len);
  
  // POST image to backend
  Serial.println("   Uploading image to backend via HTTP POST...");
  bool upload_success = uploadImageToBackend(fb);
  esp_camera_fb_return(fb);
  
  if (!upload_success) {
    Serial.println("   ⚠️  HTTP POST failed, publishing MQTT event only");
    publishMotionEvent();
  }
  
  Serial.println("🔴 Motion event handled");
}

bool uploadImageToBackend(camera_fb_t *fb) {
  if (!fb || fb->len == 0) {
    Serial.println("❌ Invalid frame buffer");
    return false;
  }
  
  WiFiClient client;
  const char* backend_host = "10.45.105.228";  // Backend IP
  const int backend_port = 5002;                 // Backend port
  
  if (!client.connect(backend_host, backend_port)) {
    Serial.printf("❌ Failed to connect to backend %s:%d\n", backend_host, backend_port);
    return false;
  }
  
  Serial.printf("✅ Connected to backend %s:%d\n", backend_host, backend_port);
  
  // Build multipart form data
  String boundary = "----FormBoundary7MA4YWxkTrZu0gW";
  String body = "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"device_id\"\r\n\r\n";
  body += String(deviceId) + "\r\n";
  body += "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"image\"; filename=\"image.jpg\"\r\n";
  body += "Content-Type: image/jpeg\r\n\r\n";
  
  // Send HTTP POST header
  String header = String("POST /upload HTTP/1.1\r\n") +
                  "Host: " + backend_host + ":" + backend_port + "\r\n" +
                  "Content-Type: multipart/form-data; boundary=" + boundary + "\r\n" +
                  "Content-Length: " + (body.length() + fb->len + boundary.length() + 16) + "\r\n" +
                  "Connection: close\r\n\r\n";
  
  client.print(header);
  client.print(body);
  client.write(fb->buf, fb->len);
  String footer = "\r\n--" + boundary + "--\r\n";
  client.print(footer);
  
  Serial.print("📤 Uploading ");
  Serial.print(fb->len);
  Serial.println(" bytes...");
  
  // Read response
  unsigned long timeout = millis() + 10000;  // 10 second timeout
  while (client.connected() && millis() < timeout) {
    if (client.available()) {
      String line = client.readStringUntil('\n');
      if (line.indexOf("200") > 0) {
        Serial.println("✅ Upload successful (HTTP 200)");
        client.stop();
        return true;
      }
    }
  }
  
  if (millis() >= timeout) {
    Serial.println("⚠️  Upload response timeout");
  }
  
  client.stop();
  return false;
}

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\n\n🔴==== ESP32-CAM STARTING ====");
  
  // 🔍 Setup PIR with debug
  pinMode(PIR_PIN, INPUT);
  Serial.printf("🔍 PIR_PIN %d initialized as INPUT\n", PIR_PIN);
  int initialPirState = digitalRead(PIR_PIN);
  Serial.printf("🔍 Initial PIR state: %d (0=LOW/no motion, 1=HIGH/motion detected)\n", initialPirState);
  
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, HIGH);
  pinMode(FLASH_LED_PIN, OUTPUT);
  digitalWrite(FLASH_LED_PIN, LOW);  // LED off initially

  connectWiFi();
  Serial.print("WiFi IP: ");
  Serial.println(WiFi.localIP());
  
  wifiClient.setInsecure();
  initTime();
  initCamera();
  
  mqttClient.setBufferSize(32768);
  connectMqtt();

  // ✅ Setup HTTP server
  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/health", HTTP_GET, handleHealth);
  server.on("/test", HTTP_GET, []() {
    Serial.println("📸 /test endpoint called - capturing test frame...");
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("❌ Test: esp_camera_fb_get() failed");
      server.send(500, "text/plain", "esp_camera_fb_get() returned NULL");
      return;
    }
    Serial.printf("✅ Test: Captured %d bytes\n", fb->len);
    server.send_P(200, "image/jpeg", (const char *)fb->buf, fb->len);
    esp_camera_fb_return(fb);
  });
  server.begin();
  Serial.println("HTTP server started on port 80 (/capture, /health, /test)");

  Serial.println("Setup complete");
}

void loop() {
  unsigned long currentTime = millis();
  int pirState = digitalRead(PIR_PIN);

  // 🔍 Debug: Log PIR state changes immediately
  if (pirState != lastPirState) {
    Serial.printf("📍 PIR STATE CHANGED: %d -> %d (at %lu ms)\n", lastPirState, pirState, currentTime);
    lastPirState = pirState;
  }
  
  // 🔍 Debug: Periodic PIR state log
  if (currentTime - lastPirDebugTime >= pirDebugInterval) {
    Serial.printf("🔍 [%lu ms] PIR state: %d, pirStable: %s, debounceWaiting: %lu ms\n", 
      currentTime, pirState, pirStable ? "true" : "false",
      pirStable ? (currentTime - pirHighStart) : 0);
    lastPirDebugTime = currentTime;
  }

  if (pirState == HIGH) {
    if (!pirStable) {
      pirHighStart = currentTime;
      pirStable = true;
      Serial.printf("📍 PIR HIGH detected at %lu ms (waiting %lu ms for debounce)\n", currentTime, debounceDelay);
    } else if (currentTime - pirHighStart >= debounceDelay) {
      Serial.printf("✅ Debounce passed: %lu ms elapsed\n", currentTime - pirHighStart);
      if (currentTime - lastTriggerTime >= cooldownPeriod) {
        Serial.println("🔴 Motion detected! Triggering capture...");
        captureAndSend();
        lastTriggerTime = currentTime;
      } else {
        unsigned long timeUntilCooldown = cooldownPeriod - (currentTime - lastTriggerTime);
        Serial.printf("⏳ Cooldown active (%d ms remaining)\n", (int)timeUntilCooldown);
      }
    }
  } else {
    if (pirStable) {
      Serial.printf("📍 PIR released at %lu ms (was stable for %lu ms)\n", currentTime, currentTime - pirHighStart);
      pirStable = false;
    }
  }

  // ✅ Handle HTTP requests
  server.handleClient();

  // Keep MQTT alive
  if (mqttClient.connected()) {
    mqttClient.loop();
  }

  delay(50);
}
