# نظام إدارة البصمات

نظام متكامل لإدارة البصمات باستخدام ESP32 وStreamlit. يتيح النظام تسجيل البصمات وإدارتها ومراقبة سجل الأحداث عبر اتصال WiFi.

## المميزات

- تسجيل بصمات جديدة
- عرض البصمات المسجلة
- حذف البصمات
- مراقبة سجل الأحداث
- لوحة معلومات تفاعلية
- اتصال لاسلكي عبر WiFi

## متطلبات التشغيل

1. **متطلبات Python**
   ```bash
   pip install -r requirements.txt
   ```

2. **متطلبات الجهاز**
   - ESP32 Development Board
   - مستشعر البصمة
   - شبكة WiFi

## إعداد الجهاز

1. **تكوين شبكة WiFi**
   - قم بتشغيل ESP32
   - اتصل بشبكة WiFi الخاصة بالجهاز (SSID: ESP32_Fingerprint)
   - افتح المتصفح على عنوان `192.168.4.1`
   - أدخل بيانات شبكة WiFi الخاصة بك

2. **التحقق من الاتصال**
   - سيعرض الجهاز عنوان IP الخاص به
   - تأكد من إمكانية الوصول إلى الجهاز عبر المتصفح

## التشغيل

1. **تشغيل التطبيق**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **الاتصال بالجهاز**
   - أدخل عنوان IP الجهاز في التطبيق
   - اضغط على زر "اتصال"
   - انتظر حتى يتم التأكيد على نجاح الاتصال

## هيكل المشروع
```
.
├── streamlit_app.py       # تطبيق Streamlit
├── requirements.txt       # متطلبات Python
├── .env.example          # نموذج الإعدادات
└── README.md             # التوثيق
```

## الأمان
- استخدم كلمة مرور قوية لشبكة WiFi
- قم بتغيير كلمة المرور الافتراضية للجهاز
- احفظ البيانات في قاعدة بيانات آمنة
- استخدم اتصالاً مشفراً مع الجهاز

## المساهمة
نرحب بمساهماتكم! يرجى اتباع الخطوات التالية:
1. Fork المشروع
2. إنشاء فرع للميزة الجديدة
3. تقديم Pull Request 