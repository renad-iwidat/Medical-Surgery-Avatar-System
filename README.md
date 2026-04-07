# 🏥 Medical Avatar OSCE Training System

نظام تدريب طبي تفاعلي للطلاب باستخدام مرضى افتراضيين مع صوت وحركة في الوقت الفعلي.

## 🌟 المميزات

- ✅ **مرضى افتراضيين واقعيين** مع حركة الشفاه والعيون (Hedra AI)
- ✅ **التعرف على الكلام العربي** في الوقت الفعلي
- ✅ **ردود ذكية** من OpenAI GPT-4o-mini
- ✅ **سيناريوهان طبيان**:
  - صباح: التهاب البنكرياس الحاد (السيد ناجي)
  - مساء: اليرقان الانسدادي (السيد حسان)
- ✅ **يدعم 10-11 طالب متزامن**
- ✅ **مؤقت تلقائي** للجلسة
- ✅ **نسخ المحادثة** في الوقت الفعلي

## 🏗️ البنية التقنية

- **Backend**: FastAPI (Python)
- **Real-time Communication**: LiveKit
- **Avatar Animation**: Hedra AI
- **Speech Recognition**: OpenAI Whisper
- **Text-to-Speech**: OpenAI TTS
- **LLM**: OpenAI GPT-4o-mini
- **Frontend**: HTML/CSS/JavaScript
- **Deployment**: Docker + Render

## 📦 التثبيت المحلي

### المتطلبات
- Python 3.11+
- pip
- Virtual environment (موصى به)

### الخطوات

1. **استنساخ المشروع**
   ```bash
   git clone YOUR_REPO_URL
   cd medical-avatar-osce
   ```

2. **إنشاء بيئة افتراضية**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # أو
   venv\Scripts\activate  # Windows
   ```

3. **تثبيت المتطلبات**
   ```bash
   pip install -r requirements.txt
   ```

4. **إعداد المتغيرات البيئية**
   ```bash
   cp .env.example .env
   # ثم عدل .env وأضف مفاتيحك
   ```

5. **تشغيل النظام**
   
   في نافذة Terminal الأولى (LiveKit Agent):
   ```bash
   python livekit_agent.py start
   ```
   
   في نافذة Terminal الثانية (Backend):
   ```bash
   python main.py
   ```

6. **افتح المتصفح**
   ```
   http://localhost:8000
   ```

## 🐳 التشغيل باستخدام Docker

### محلياً

```bash
# بناء وتشغيل
docker-compose up --build

# في الخلفية
docker-compose up -d

# إيقاف
docker-compose down
```

### على Render

راجع [دليل النشر](DEPLOYMENT.md) للتفاصيل الكاملة.

## 📁 هيكل المشروع

```
medical-avatar-osce/
├── main.py                 # FastAPI backend
├── livekit_agent.py        # LiveKit agent with Hedra
├── prompts.py              # System prompts
├── session_manager.py      # Session management
├── scenario_manager.py     # Scenario loading
├── livekit_routes.py       # LiveKit API routes
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── start.sh                # Startup script
├── render.yaml             # Render deployment config
├── scenarios/
│   ├── case-morning.json   # Morning scenario
│   └── case-evening.json   # Evening scenario
├── img/
│   ├── avatar-morning.jpeg # Morning patient avatar
│   └── avatar-evening.png  # Evening patient avatar
└── public/
    ├── index-livekit.html  # Main frontend
    ├── app-livekit.js      # Frontend logic
    ├── livekit-client.js   # LiveKit client wrapper
    └── style.css           # Styles
```

## 🎮 كيفية الاستخدام

1. **افتح الصفحة الرئيسية**
2. **اختر السيناريو** (صباح أو مساء)
3. **أدخل كلمة المرور**: `surgery2024`
4. **أدخل اسمك والقسم**
5. **اضغط "ابدأ الجلسة"**
6. **استمع للمريض** وهو يقدم نفسه
7. **اضغط مسافة** للتحدث
8. **اسأل أسئلتك** بالعربية
9. **استمع للإجابات** من المريض الافتراضي

## 🔑 المتغيرات البيئية

| المتغير | الوصف | مطلوب |
|---------|-------|-------|
| `OPENAI_API_KEY` | مفتاح OpenAI للـ LLM | ✅ |
| `OPENAI_TTS_API_KEY` | مفتاح OpenAI للصوت | ✅ |
| `HEDRA_API_KEY` | مفتاح Hedra للأفاتار | ✅ |
| `LIVEKIT_URL` | رابط LiveKit Cloud | ✅ |
| `LIVEKIT_API_KEY` | مفتاح LiveKit API | ✅ |
| `LIVEKIT_API_SECRET` | سر LiveKit API | ✅ |
| `ELEVENLABS_API_KEY` | مفتاح ElevenLabs (اختياري) | ❌ |
| `PORT` | بورت الخادم (افتراضي: 8000) | ❌ |

## 🧪 الاختبار

### اختبار Health Check
```bash
curl http://localhost:8000/api/health
```

### اختبار Scenarios API
```bash
curl http://localhost:8000/api/scenarios
```

### اختبار LiveKit Token
```bash
curl -X POST http://localhost:8000/api/livekit/token \
  -H "Content-Type: application/json" \
  -d '{"roomName":"test-room","participantName":"test-user"}'
```

## 📊 الأداء

- **الطلاب المتزامنين**: 10-11
- **زمن الاستجابة**: 1-3 ثواني
- **استهلاك الذاكرة**: ~500MB
- **استهلاك CPU**: متوسط

## 🔧 استكشاف الأخطاء

### المشكلة: الصوت لا يعمل
- تأكد من السماح للمتصفح بالوصول للميكروفون
- استخدم Chrome أو Edge (موصى به)
- تحقق من مفاتيح OpenAI و Hedra

### المشكلة: الأفاتار لا يتحرك
- تحقق من `HEDRA_API_KEY`
- راجع Logs للبحث عن أخطاء Hedra
- تأكد من أن صور الأفاتار موجودة في `img/`

### المشكلة: الردود بطيئة
- تحقق من اتصال الإنترنت
- راجع استهلاك OpenAI API
- زد Instance Type على Render

## 📝 السيناريوهات

### السيناريو الصباحي: التهاب البنكرياس الحاد
- **المريض**: ناجي (35 سنة، مهندس)
- **الشكوى**: ألم بطني حاد منذ 12 ساعة
- **التشخيص**: التهاب البنكرياس الحاد
- **الصورة**: `img/avatar-morning.jpeg`

### السيناريو المسائي: اليرقان الانسدادي
- **المريض**: حسان (58 سنة، معلم)
- **الشكوى**: اصفرار الجلد والعينين
- **التشخيص**: اليرقان الانسدادي
- **الصورة**: `img/avatar-evening.png`

## 🔐 الأمان

- كلمة المرور الافتراضية: `surgery2024` (غيرها في الإنتاج!)
- لا ترفع ملف `.env` إلى GitHub
- استخدم HTTPS في الإنتاج
- حدد الوصول باستخدام IP Whitelist إذا لزم الأمر

## 🚀 النشر

راجع [دليل النشر الكامل](DEPLOYMENT.md) للتفاصيل.

### نشر سريع على Render

1. رفع إلى GitHub
2. ربط Render بالمستودع
3. إضافة المتغيرات البيئية
4. النشر تلقائياً!

## 📞 الدعم

للمشاكل التقنية:
1. راجع Logs
2. تحقق من المتغيرات البيئية
3. اختبر محلياً أولاً

## 📄 الترخيص

هذا المشروع للاستخدام التعليمي في كلية الطب.

## 🙏 شكر وتقدير

- **OpenAI** - GPT-4o-mini & Whisper & TTS
- **LiveKit** - Real-time communication
- **Hedra AI** - Avatar animation
- **Render** - Hosting platform

---

**تم التطوير بواسطة**: فريق التدريب الطبي
**الإصدار**: 1.0
**التاريخ**: أبريل 2026
