# تعليمات تثبيت وتشغيل برنامج التحكم في البصمة

## متطلبات الأردوينو
1. تثبيت المكتبات التالية من مدير المكتبات في Arduino IDE:
   - Adafruit Fingerprint Sensor Library
   - ESP32 Arduino Core

## توصيل الأجهزة
1. توصيل مستشعر البصمة مع ESP32:
   - VCC -> 3.3V أو 5V (حسب نوع المستشعر)
   - GND -> GND
   - TX -> GPIO16 (RX2)
   - RX -> GPIO17 (TX2)

## خطوات التثبيت
1. فتح Arduino IDE
2. اختيار نوع اللوحة: Tools -> Board -> ESP32 -> ESP32 Dev Module
3. اختيار المنفذ: Tools -> Port -> COM* (Windows) أو /dev/ttyUSB* (Linux)
4. تحميل البرنامج على اللوحة

## ملاحظات هامة
- تأكد من تثبيت حزمة ESP32 في Arduino IDE
- يمكن تثبيت الحزمة من خلال:
  1. فتح Arduino IDE
  2. الذهاب إلى File -> Preferences
  3. إضافة الرابط التالي في Additional Boards Manager URLs:
     `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
  4. فتح Tools -> Board -> Boards Manager
  5. البحث عن "esp32" وتثبيت الحزمة 