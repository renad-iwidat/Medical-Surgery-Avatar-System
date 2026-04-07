# 🚀 دليل النشر - Medical Avatar OSCE Training System

## نظرة عامة
هذا الدليل يشرح كيفية نشر نظام التدريب الطبي على Render باستخدام Docker.

---

## 📋 المتطلبات الأساسية

1. حساب على [Render.com](https://render.com)
2. حساب على [GitHub](https://github.com) (لربط المشروع)
3. المفاتيح التالية جاهزة:
   - `OPENAI_API_KEY`
   - `OPENAI_TTS_API_KEY`
   - `ELEVENLABS_API_KEY`
   - `HEDRA_API_KEY`
   - `LIVEKIT_URL`
   - `LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET`

---

## 🧪 الاختبار المحلي (قبل النشر)

### 1. اختبار Docker محلياً

```bash
# بناء الصورة
docker build -t medical-avatar .

# تشغيل الحاوية
docker run -p 8000:8000 --env-file .env medical-avatar

# اختبار الصحة
curl http://localhost:8000/api/health
```

### 2. اختبار Docker Compose

```bash
# تشغيل جميع الخدمات
docker-compose up --build

# في نافذة أخرى، اختبر
curl http://localhost:8000/api/health
```

### 3. التحقق من الخدمات

افتح المتصفح على:
- Frontend: http://localhost:8000
- Health Check: http://localhost:8000/api/health
- Scenarios: http://localhost:8000/api/scenarios

---

## 🌐 النشر على Render

### الطريقة 1: استخدام render.yaml (موصى بها)

1. **رفع المشروع إلى GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Medical Avatar OSCE"
   git branch -M main
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **إنشاء خدمة جديدة على Render**
   - اذهب إلى [Render Dashboard](https://dashboard.render.com)
   - اضغط "New +" → "Blueprint"
   - اربط مستودع GitHub الخاص بك
   - Render سيكتشف ملف `render.yaml` تلقائياً

3. **إضافة المتغيرات البيئية**
   في لوحة Render، أضف المتغيرات التالية:
   ```
   OPENAI_API_KEY=sk-proj-...
   OPENAI_TTS_API_KEY=sk-proj-...
   ELEVENLABS_API_KEY=sk_...
   HEDRA_API_KEY=sk_hedra_...
   LIVEKIT_URL=https://medical-avatar-80f5hu67.livekit.cloud
   LIVEKIT_API_KEY=APIfRpRSSXXDqKe
   LIVEKIT_API_SECRET=bUQbsR72qGoNDKxyYXTuFhfAGOA0Ml2gtCBU29LqfsP
   ```

4. **انتظر النشر**
   - Render سيبني الصورة تلقائياً
   - سيستغرق 5-10 دقائق للنشر الأول
   - ستحصل على رابط مثل: `https://medical-avatar-osce.onrender.com`

### الطريقة 2: النشر اليدوي

1. **إنشاء Web Service جديد**
   - New + → Web Service
   - اختر "Docker"
   - اربط GitHub repo

2. **إعدادات الخدمة**
   - Name: `medical-avatar-osce`
   - Region: Frankfurt (أقرب للشرق الأوسط)
   - Branch: `main`
   - Dockerfile Path: `./Dockerfile`
   - Docker Context: `.`

3. **إعدادات متقدمة**
   - Instance Type: Starter ($7/month) أو أعلى
   - Health Check Path: `/api/health`
   - Auto-Deploy: Yes

4. **أضف المتغيرات البيئية** (نفس القائمة أعلاه)

---

## ✅ التحقق من النشر

بعد النشر الناجح:

1. **اختبار Health Check**
   ```bash
   curl https://YOUR-APP.onrender.com/api/health
   ```
   يجب أن يرجع: `{"status":"ok","service":"Medical Avatar Surgery"}`

2. **اختبار Scenarios API**
   ```bash
   curl https://YOUR-APP.onrender.com/api/scenarios
   ```

3. **افتح الواجهة الأمامية**
   - اذهب إلى: `https://YOUR-APP.onrender.com`
   - اختر سيناريو (صباح أو مساء)
   - أدخل كلمة المرور: `surgery2024`
   - ابدأ الجلسة

---

## 🔧 استكشاف الأخطاء

### المشكلة: الخدمة لا تبدأ

**الحل:**
1. تحقق من Logs في Render Dashboard
2. تأكد من جميع المتغيرات البيئية موجودة
3. تحقق من أن `start.sh` قابل للتنفيذ

### المشكلة: Health Check يفشل

**الحل:**
```bash
# تحقق من أن البورت 8000 يعمل
# في Render Logs، ابحث عن:
# "Uvicorn running on http://0.0.0.0:8000"
```

### المشكلة: LiveKit Agent لا يتصل

**الحل:**
1. تحقق من `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
2. تأكد من أن LiveKit Cloud يعمل
3. راجع Logs للبحث عن أخطاء الاتصال

### المشكلة: الصوت لا يعمل

**الحل:**
1. تحقق من `OPENAI_API_KEY` و `HEDRA_API_KEY`
2. تأكد من أن المتصفح يسمح بالميكروفون
3. جرب متصفح مختلف (Chrome موصى به)

---

## 📊 المراقبة والصيانة

### عرض Logs
```bash
# في Render Dashboard:
# اذهب إلى Service → Logs
# أو استخدم Render CLI:
render logs -f
```

### إعادة النشر
```bash
# عند تحديث الكود:
git add .
git commit -m "Update message"
git push origin main

# Render سينشر تلقائياً إذا كان Auto-Deploy مفعل
```

### التوسع (Scaling)
- للتعامل مع 10-11 طالب متزامن، استخدم:
  - Instance Type: Starter أو أعلى
  - إذا كان الأداء بطيء، ارفع إلى Standard

---

## 💰 التكلفة المتوقعة

- **Render Starter Plan**: $7/شهر
- **LiveKit Cloud**: مجاني حتى 50 ساعة/شهر
- **OpenAI API**: ~$0.01-0.05 لكل جلسة
- **Hedra API**: حسب الاستخدام

**التكلفة الإجمالية المتوقعة**: $10-15/شهر لـ 100-200 جلسة

---

## 🔐 الأمان

1. **لا ترفع ملف `.env` إلى GitHub**
   - الملف موجود في `.gitignore`
   - استخدم Render Environment Variables

2. **غير كلمة المرور**
   - الكلمة الحالية: `surgery2024`
   - غيرها في `public/app-livekit.js`

3. **حدد الوصول**
   - استخدم Render's IP Whitelist إذا لزم الأمر
   - أضف Authentication إضافي إذا كان مطلوباً

---

## 📞 الدعم

إذا واجهت مشاكل:
1. راجع Render Logs
2. تحقق من LiveKit Dashboard
3. اختبر محلياً أولاً باستخدام Docker

---

## ✨ ملاحظات مهمة

- ✅ النظام يدعم 10-11 طالب متزامن
- ✅ الصوت والفيديو في الوقت الفعلي مع Hedra
- ✅ التعرف على الكلام العربي
- ✅ سيناريوهان: صباح (التهاب البنكرياس) ومساء (اليرقان الانسدادي)
- ✅ Health checks تلقائية
- ✅ Auto-deploy عند Push إلى GitHub

---

**تم إنشاء هذا الدليل في**: أبريل 2026
**الإصدار**: 1.0
