#define MQTT_MAX_PACKET_SIZE 262144
#include <WiFi.h>
#include <WiFiClient.h>
#include <PubSubClient.h>
#include <esp_camera.h>
#include <time.h>

// Pin definitions
#define PIR_PIN 13        // PIR sensor pin
#define BUZZER_PIN 14     // Buzzer pin (LOW active)

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
const char* ssid = "Nhut Khanh";
const char* password = "Nhutkhanh2020";

// MQTT config
const char* mqttBroker = "47aba3e9f3f94aa8b2f163688423010c.s1.eu.hivemq.cloud";
const int mqttPort = 1883;
const char* mqttUser = "esp32cam2";
const char* mqttPassword = "Nhutkhanh2025";
const char* deviceId = "cam2";
String mqttTopic = String("camera/") + deviceId + "/motion";

// Timing variables
unsigned long lastTriggerTime = 0;
const unsigned long cooldownPeriod = 15000; // 15 seconds cooldown
const unsigned long debounceDelay = 2000;   // 2 seconds debounce
unsigned long pirHighStart = 0;
bool pirStable = false;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

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

String base64Encode(const uint8_t *data, size_t inputLen) {
  String encoded;
  encoded.reserve(((inputLen + 2) / 3) * 4);

  uint8_t char_array_3[3];
  uint8_t char_array_4[4];
  int i = 0;

  while (inputLen--) {
    char_array_3[i++] = *(data++);
    if (i == 3) {
      char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
      char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
      char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);
      char_array_4[3] = char_array_3[2] & 0x3f;

      for (i = 0; i < 4; i++) {
        encoded += base64Chars[char_array_4[i]];
      }
      i = 0;
    }
  }

  if (i > 0) {
    for (int j = i; j < 3; j++) {
      char_array_3[j] = '\0';
    }

    char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
    char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
    char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);
    char_array_4[3] = char_array_3[2] & 0x3f;

    for (int j = 0; j < i + 1; j++) {
      encoded += base64Chars[char_array_4[j]];
    }

    while ((i++ < 3)) {
      encoded += '=';
    }
  }

  return encoded;
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
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
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
  mqttClient.setBufferSize(262144);

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

String buildPayload(camera_fb_t *fb) {
  String payload = "{";
  payload += String("\"device_id\": \"") + deviceId + "\",";
  payload += String("\"timestamp\": \"") + getTimestamp() + "\",";
  payload += String("\"image\": \"") + base64Encode(fb->buf, fb->len) + "\"";
  payload += "}";
  return payload;
}

void publishMotionEvent(camera_fb_t *fb) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, cannot publish MQTT event");
    return;
  }

  if (!mqttClient.connected()) {
    connectMqtt();
  }

  mqttClient.loop();
  String payload = buildPayload(fb);
  bool published = mqttClient.publish(mqttTopic.c_str(), payload.c_str());
  if (published) {
    Serial.println("MQTT motion event published");
  } else {
    Serial.println("MQTT publish failed");
  }
}

void captureAndSend() {
  digitalWrite(BUZZER_PIN, LOW);
  delay(1000);

  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    digitalWrite(BUZZER_PIN, HIGH);
    return;
  }

  publishMotionEvent(fb);
  esp_camera_fb_return(fb);
  digitalWrite(BUZZER_PIN, HIGH);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIR_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, HIGH);

  connectWiFi();
  initTime();
  initCamera();
  mqttClient.setServer(mqttBroker, mqttPort);
  mqttClient.setBufferSize(262144);

  Serial.println("Setup complete");
}

void loop() {
  unsigned long currentTime = millis();
  int pirState = digitalRead(PIR_PIN);

  if (pirState == HIGH) {
    if (!pirStable) {
      pirHighStart = currentTime;
      pirStable = true;
    } else if (currentTime - pirHighStart >= debounceDelay) {
      if (currentTime - lastTriggerTime >= cooldownPeriod) {
        Serial.println("Motion detected, capturing image...");
        captureAndSend();
        lastTriggerTime = currentTime;
      }
    }
  } else {
    pirStable = false;
  }

  if (mqttClient.connected()) {
    mqttClient.loop();
  }

  delay(100);
}
