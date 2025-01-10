#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <Adafruit_Fingerprint.h>
#include <HardwareSerial.h>

// WiFi settings
const char* ssid = "ccc";
const char* password = "00000000";

// Network settings
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// Pin Definitions
#define RST_PIN         5    
#define SS_PIN          22   
#define LDR_PIN         34
#define RELAY_LID       26
#define RELAY_LOCK      27

// RFID
MFRC522 mfrc522(SS_PIN, RST_PIN);

// Fingerprint sensor
HardwareSerial mySerial(2); // Use Hardware Serial 2 for ESP32
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

// Global variables
uint8_t id;
volatile int finger_status = -1;
int is_stored_new_fingerprint = 0;
int fingerprint_ID = 0;
String message = "";

void setup() {
  Serial.begin(115200);

  // Initialize WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");

  // Initialize MQTT
  mqttClient.setServer("broker.hivemq.com", 1883);
  mqttClient.setCallback(callback);

  // Initialize RFID
  SPI.begin();
  mfrc522.PCD_Init();
  
  // Initialize Fingerprint sensor
  mySerial.begin(57600, SERIAL_8N1, 16, 17); // RX=16, TX=17
  finger.begin(57600);
  if (finger.verifyPassword()) {
    Serial.println("Found fingerprint sensor!");
  } else {
    Serial.println("Did not find fingerprint sensor");
    while (1) { delay(1); }
  }

  // Initialize pins
  pinMode(LDR_PIN, INPUT);
  pinMode(RELAY_LID, OUTPUT);
  pinMode(RELAY_LOCK, OUTPUT);
  digitalWrite(RELAY_LID, LOW);
  digitalWrite(RELAY_LOCK, LOW);
}

void loop() {
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop();

  // Read LDR
  int lightLevel = analogRead(LDR_PIN);
  Serial.println("Light level: " + String(lightLevel));
  if (lightLevel < 500) {
    digitalWrite(RELAY_LID, HIGH);
  } else {
    digitalWrite(RELAY_LID, LOW);
  }

  // Check fingerprint
  finger_status = getFingerprintID();
  if (finger_status != -1 && finger_status != -2) {
    Serial.println("Fingerprint match found: " + String(finger_status));
    mqttClient.publish("qou/hebron/pro/smartControlEntrance/fingerprint_msg", "correct fingerprint_ID");
  }

  delay(100);
}

void reconnect() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (mqttClient.connect("ArduinoClient")) {
      Serial.println("connected");
      mqttClient.subscribe("qou/hebron/pro/smartControlEntrance/1");
      mqttClient.subscribe("qou/hebron/pro/smartControlEntrance/2");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println("Message received: " + String(topic) + " " + message);
}

int getFingerprintID() {
  uint8_t p = finger.getImage();
  if (p != FINGERPRINT_OK) return -1;

  p = finger.image2Tz();
  if (p != FINGERPRINT_OK) return -1;

  p = finger.fingerFastSearch();
  if (p != FINGERPRINT_OK) return -2;

  return finger.fingerID;
}

uint8_t getFingerprintEnroll() {
  int p = -1;
  Serial.println("Waiting for valid finger to enroll");
  
  while (p != FINGERPRINT_OK) {
    p = finger.getImage();
    if (p == FINGERPRINT_OK) {
      Serial.println("Image taken");
      break;
    }
    delay(100);
  }

  p = finger.image2Tz(1);
  if (p != FINGERPRINT_OK) return p;

  Serial.println("Remove finger");
  delay(2000);
  
  p = 0;
  while (p != FINGERPRINT_NOFINGER) {
    p = finger.getImage();
  }

  Serial.println("Place same finger again");
  
  p = -1;
  while (p != FINGERPRINT_OK) {
    p = finger.getImage();
    delay(100);
  }

  p = finger.image2Tz(2);
  if (p != FINGERPRINT_OK) return p;

  p = finger.createModel();
  if (p != FINGERPRINT_OK) return p;

  p = finger.storeModel(id);
  if (p == FINGERPRINT_OK) {
    Serial.println("Stored!");
    is_stored_new_fingerprint = 1;
    return 1;
  }
  return p;
}
