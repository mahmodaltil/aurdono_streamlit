#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_Fingerprint.h>

// إعدادات WiFi
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// إعدادات API
const char* api_url = "YOUR_API_URL";  // مثال: http://your-app.streamlit.app/api
const char* device_id = "ESP32_001";   // معرف فريد للجهاز

// إعدادات مستشعر البصمة
#define FINGERPRINT_RX 16
#define FINGERPRINT_TX 17
HardwareSerial fingerSerial(2);
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&fingerSerial);

void setup() {
  Serial.begin(115200);
  
  // اتصال WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  
  // تهيئة مستشعر البصمة
  fingerSerial.begin(57600, SERIAL_8N1, FINGERPRINT_RX, FINGERPRINT_TX);
  finger.begin(57600);
  
  if (finger.verifyPassword()) {
    Serial.println("Found fingerprint sensor!");
    registerDevice();
  } else {
    Serial.println("Did not find fingerprint sensor :(");
  }
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    getFingerprintID();
    delay(50);
  }
}

void registerDevice() {
  HTTPClient http;
  http.begin(String(api_url) + "/devices");
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;
  doc["device_id"] = device_id;
  doc["name"] = "ESP32 Fingerprint Sensor";
  doc["status"] = "online";
  doc["last_seen"] = "now";
  doc["connection_type"] = "wifi";
  doc["ip_address"] = WiFi.localIP().toString();
  
  String requestBody;
  serializeJson(doc, requestBody);
  
  int httpResponseCode = http.POST(requestBody);
  if (httpResponseCode > 0) {
    Serial.println("Device registered successfully");
  } else {
    Serial.println("Error registering device");
  }
  http.end();
}

void sendFingerprintData(int fingerprintID, float confidence) {
  HTTPClient http;
  http.begin(String(api_url) + "/fingerprints");
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;
  doc["device_id"] = device_id;
  doc["fingerprint_id"] = fingerprintID;
  doc["timestamp"] = "now";
  doc["confidence"] = confidence;
  
  String requestBody;
  serializeJson(doc, requestBody);
  
  int httpResponseCode = http.POST(requestBody);
  if (httpResponseCode > 0) {
    Serial.println("Fingerprint data sent successfully");
  } else {
    Serial.println("Error sending fingerprint data");
  }
  http.end();
}

uint8_t getFingerprintID() {
  uint8_t p = finger.getImage();
  if (p != FINGERPRINT_OK) return p;
  
  p = finger.image2Tz();
  if (p != FINGERPRINT_OK) return p;
  
  p = finger.fingerFastSearch();
  if (p == FINGERPRINT_OK) {
    Serial.print("Found ID #"); Serial.print(finger.fingerID);
    Serial.print(" with confidence of "); Serial.println(finger.confidence);
    sendFingerprintData(finger.fingerID, finger.confidence);
  }
  return p;
} 