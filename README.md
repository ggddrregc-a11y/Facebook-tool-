# 🤖 Remix AI — نظام الرد التلقائي على تعليقات فيسبوك

نظام متكامل للرد التلقائي على تعليقات صفحة فيسبوك باستخدام الذكاء الاصطناعي.  
مبني بـ Python + FastAPI + PostgreSQL، جاهز للنشر على Railway.

---

## 📋 المميزات

- ✅ رد تلقائي فوري على تعليقات فيسبوك
- ✅ كشف المشاعر (دعاء، حزن، فرح، حب، إعجاب، سؤال، غضب، إيموجي، محايد)
- ✅ كشف السبام والروابط والمحتوى الترويجي
- ✅ كشف التعليقات المكررة وإعادة استخدام الردود
- ✅ ذكاء اصطناعي مرن (OpenRouter / OpenAI / أي مزود متوافق)
- ✅ لوحة تحكم عربية داكنة احترافية
- ✅ معالجة في الخلفية (Webhook يرجع 200 فوراً)
- ✅ تسجيل كامل للأحداث والأخطاء
- ✅ جاهز للنشر على Railway

---

## 🚀 التثبيت المحلي

### المتطلبات
- Python 3.12
- PostgreSQL
- Docker (اختياري)

### الخطوات

```bash
# 1. نسخ المشروع
git clone <repo-url>
cd remix-ai

# 2. إنشاء البيئة الافتراضية
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 3. تثبيت المكتبات
pip install -r requirements.txt

# 4. نسخ ملف الإعدادات
cp .env.example .env

# 5. تعديل .env بقيمك الحقيقية

# 6. تشغيل التطبيق
uvicorn app.main:app --reload --port 8000
```

---

## 🐳 التشغيل بـ Docker

```bash
# نسخ وتعديل .env
cp .env.example .env

# تشغيل الكل
docker-compose up -d

# عرض السجلات
docker-compose logs -f app
```

---

## 🚂 النشر على Railway

### الطريقة الأولى: من GitHub

1. ادفع الكود إلى GitHub
2. افتح [railway.app](https://railway.app)
3. اضغط **New Project → Deploy from GitHub Repo**
4. اختر المستودع
5. أضف قاعدة بيانات: **Add Service → PostgreSQL**
6. في تبويب **Variables** أضف متغيرات البيئة (انظر قسم المتغيرات)
7. في متغير `DATABASE_URL` استخدم القيمة من Railway PostgreSQL تلقائياً

### الطريقة الثانية: Railway CLI

```bash
# تثبيت CLI
npm i -g @railway/cli

# تسجيل الدخول
railway login

# ربط المشروع
railway link

# نشر
railway up

# إضافة PostgreSQL
railway add postgresql

# إضافة المتغيرات
railway variables set APP_SECRET=xxx VERIFY_TOKEN=xxx ...
```

### متغير DATABASE_URL على Railway

Railway يوفر متغير `DATABASE_URL` تلقائياً عند إضافة PostgreSQL.  
لكن يجب تغيير `postgresql://` إلى `postgresql+asyncpg://`:

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

---

## ⚙️ متغيرات البيئة

| المتغير | الوصف | مثال |
|---------|-------|------|
| `APP_SECRET` | مفتاح التطبيق السري (32 حرف+) | `my_super_secret_key_32_chars_min` |
| `VERIFY_TOKEN` | رمز التحقق للـ Webhook | `my_webhook_verify_token` |
| `PAGE_ACCESS_TOKEN` | توكن وصول صفحة فيسبوك | `EAABxxxxx...` |
| `DATABASE_URL` | رابط قاعدة البيانات | `postgresql+asyncpg://...` |
| `OPENAI_API_KEY` | مفتاح OpenRouter أو OpenAI | `sk-or-xxxxx` |
| `OPENAI_BASE_URL` | رابط مزود الذكاء الاصطناعي | `https://openrouter.ai/api/v1` |
| `MODEL_NAME` | اسم النموذج | `qwen/qwen3-8b:free` |
| `JWT_SECRET` | مفتاح JWT (32 حرف+) | `jwt_secret_key_here` |
| `ADMIN_USERNAME` | اسم مستخدم لوحة التحكم | `admin` |
| `ADMIN_PASSWORD` | كلمة مرور لوحة التحكم | `StrongPass123!` |
| `SECRET_KEY` | مفتاح التطبيق | `secret_key_here` |
| `LOG_LEVEL` | مستوى التسجيل | `INFO` |
| `CACHE_ENABLED` | تفعيل Redis Cache | `false` |

---

## 📱 إعداد فيسبوك

### الخطوة 1: إنشاء تطبيق فيسبوك

1. افتح [developers.facebook.com](https://developers.facebook.com)
2. اضغط **My Apps → Create App**
3. اختر **Business** ثم أدخل اسم التطبيق
4. من القائمة الجانبية اختر **Messenger → Settings**

### الخطوة 2: الحصول على Page Access Token

1. في صفحة إعدادات Messenger
2. في **Access Tokens** اختر صفحتك
3. اضغط **Generate Token** وانسخ القيمة
4. ضعها في `PAGE_ACCESS_TOKEN`

### الخطوة 3: إعداد Webhook

1. في **Webhooks** اضغط **Add Callback URL**
2. أدخل: `https://your-app.railway.app/webhook`
3. في **Verify Token** أدخل نفس قيمة `VERIFY_TOKEN` في `.env`
4. اضغط **Verify and Save**
5. في **Subscription Fields** فعّل: `feed`
6. اضغط **Subscribe to this object** واختر صفحتك

### الخطوة 4: صلاحيات التطبيق

تأكد من وجود هذه الصلاحيات:
- `pages_read_engagement`
- `pages_manage_posts`
- `pages_manage_engagement`

---

## 🎮 استخدام لوحة التحكم

1. افتح: `https://your-app.railway.app/login`
2. سجّل الدخول بـ `ADMIN_USERNAME` و `ADMIN_PASSWORD`
3. ستجد:
   - **لوحة التحكم**: إحصائيات شاملة ورسوم بيانية
   - **التعليقات**: جميع التعليقات مع البحث والتصفية
   - **سجل الأحداث**: سجل كامل للأحداث والأخطاء
   - **اختبار الرد**: جرّب الذكاء الاصطناعي مباشرة

---

## 🔌 تغيير مزود الذكاء الاصطناعي

فقط عدّل `.env`:

```bash
# OpenRouter (افتراضي)
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=sk-or-xxxxx
MODEL_NAME=qwen/qwen3-8b:free

# OpenAI
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-xxxxx
MODEL_NAME=gpt-4o-mini

# Groq
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_API_KEY=gsk_xxxxx
MODEL_NAME=llama-3.1-8b-instant

# خادم محلي (Ollama)
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
MODEL_NAME=qwen2.5:7b
```

---

## 🛠️ حل المشاكل الشائعة

### المشكلة: الـ Webhook لا يتحقق

```
تأكد من:
- VERIFY_TOKEN في .env مطابق لما أدخلته في فيسبوك
- الرابط يعمل: https://your-app/health → يجب أن يرجع {"status":"ok"}
- الـ SSL يعمل (Railway يوفره تلقائياً)
```

### المشكلة: لا يتم الرد على التعليقات

```
تحقق من:
1. /dashboard/logs للأخطاء
2. PAGE_ACCESS_TOKEN صحيح وغير منتهي
3. صلاحيات الصفحة (pages_manage_engagement)
4. OPENAI_API_KEY صحيح
```

### المشكلة: خطأ في قاعدة البيانات

```
تأكد من:
- DATABASE_URL يستخدم postgresql+asyncpg:// (وليس postgresql://)
- قاعدة البيانات تعمل وقابلة للوصول
- على Railway: استخدم المتغير المقدم من Railway PostgreSQL
```

### المشكلة: لا يمكن تسجيل الدخول

```
تأكد من:
- ADMIN_USERNAME و ADMIN_PASSWORD صحيحان في .env
- التطبيق يعمل وقاعدة البيانات متصلة
```

---

## 📡 API Endpoints

| الطريقة | المسار | الوصف |
|---------|--------|-------|
| GET | `/health` | فحص صحة النظام |
| GET | `/webhook` | تحقق Webhook |
| POST | `/webhook` | استقبال أحداث فيسبوك |
| POST | `/api/auth/login` | تسجيل الدخول |
| POST | `/api/auth/logout` | تسجيل الخروج |
| GET | `/api/stats` | إحصائيات النظام |
| GET | `/api/comments` | قائمة التعليقات |
| POST | `/api/reply-test` | اختبار الرد |
| GET | `/api/logs` | سجل الأحداث |
| GET | `/docs` | توثيق Swagger |

---

## 🏗️ هيكل المشروع

```
app/
├── api/           # API endpoints و dashboard routes
├── ai/            # مزود الذكاء الاصطناعي، كشف المشاعر، كشف السبام
├── config/        # إعدادات التطبيق
├── core/          # الأساسيات (logging, security, exceptions)
├── database/      # إدارة قاعدة البيانات
├── facebook/      # عميل Facebook Graph API
├── middlewares/   # المصادقة، التسجيل
├── models/        # نماذج SQLAlchemy
├── repositories/  # طبقة الوصول للبيانات
├── schemas/       # Pydantic schemas
├── services/      # منطق العمل
├── templates/     # قوالب HTML
├── workers/       # معالجة الخلفية
└── main.py        # نقطة بداية التطبيق
```

---

## 📄 الترخيص

هذا المشروع لأغراض تجارية. جميع الحقوق محفوظة.
