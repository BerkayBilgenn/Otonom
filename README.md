# 📞 AI Çağrı Merkezi Asistanı

> Yapay Zeka Destekli Sesli Randevu Yönetim Sistemi

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-AI-4285F4?style=flat-square&logo=google&logoColor=white)
![Google Calendar](https://img.shields.io/badge/Google_Calendar-API-EA4335?style=flat-square&logo=googlecalendar&logoColor=white)

---

**Doğal dil ile konuşarak randevu alın, iptal edin ve takviminizi yönetin.**  
Gerçek zamanlı sesli iletişim • Google Calendar entegrasyonu • Akıllı müsaitlik kontrolü

---

## 🧠 Proje Hakkında

**AI Çağrı Merkezi Asistanı**, Google Gemini 2.5 Flash AI modeli üzerine inşa edilmiş, sesli ve yazılı iletişim ile çalışan akıllı bir randevu yönetim sistemidir.

Kullanıcılar doğal Türkçe konuşarak veya yazarak:

- 📅 **Randevu oluşturabilir** — *"Yarın saat 14:00'te kayıt olmak istiyorum"*
- 🕐 **Müsaitlik sorgulayabilir** — *"Cuma günü boş saatleri göster"*
- ❌ **Randevu iptal edebilir** — *"Saat 16:00'daki randevumu iptal et"*
- 🎨 **Görsel prompt üretebilir** — *"Karda koşan atlar için bir prompt hazırla"*

Sistem, **Google Calendar API** ile gerçek zamanlı senkronize çalışır — oluşturulan randevular doğrudan Google Takvim'e eklenir.

---

## ✨ Özellikler

### Çekirdek

| Özellik | Açıklama |
|:---|:---|
| 🎙️ Sesli Asistan | Web Speech API ile Türkçe ses tanıma (STT) |
| 🔊 Sesli Yanıt | Google Cloud WaveNet TTS ile doğal sesli yanıt |
| 🤖 Gemini AI | Gemini 2.5 Flash — doğal dil anlama + function calling |
| 📅 Takvim | Google Calendar API ile gerçek zamanlı randevu yönetimi |
| ✅ Müsaitlik | Otomatik çakışma tespiti ve alternatif saat önerileri |
| 🎨 Prompt Enhancer | Hunyuan 7B ile görsel prompt zenginleştirme *(opsiyonel)* |

### Arayüz

| Özellik | Açıklama |
|:---|:---|
| 🌙 Karanlık Tema | Premium dark UI, glassmorphism efektleri |
| ✨ Particle Animasyonu | Canvas üzerinde canlı parçacık arka planı |
| 📱 Responsive | Masaüstü ve mobil uyumlu sidebar navigasyon |
| 💬 Sohbet Paneli | Modern chat bubble UI, hızlı eylem butonları |
| 📋 Takvim Paneli | Yaklaşan randevuları görüntüleme paneli |

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────┐
│                     FRONTEND                         │
│   Web Speech API (STT) ← → Chat UI ← → Calendar    │
│                      ↕ HTTP REST                     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│                BACKEND (FastAPI)                      │
│                                                      │
│   main.py ─── /api/chat ─── /api/appointments        │
│       │                          │                    │
│   gemini_service.py      calendar_service.py          │
│   (Gemini 2.5 Flash)    (Google Calendar API)         │
│   (Function Calling)    (Check/Book/Cancel)           │
│       │                                               │
│   prompt_enhancer_service.py (Hunyuan 7B, opsiyonel)  │
└──────────────────────────────────────────────────────┘
```

### Akış

```
Kullanıcı → "Yarın 14:00'te randevu al"
         → Frontend → POST /api/chat → Gemini AI
         → Gemini: function_call → check_calendar_availability
         → Calendar API → "Müsait ✅"
         → Gemini: function_call → book_appointment
         → Calendar API → "Randevu oluşturuldu"
         → Gemini → "Randevunuz başarıyla oluşturuldu!"
         → Frontend → Chat + TTS sesli yanıt → Kullanıcı
```

---

## 🛠️ Teknoloji Stack

**Backend:** Python 3.10+ · FastAPI · Uvicorn · Google Generative AI SDK · Google Calendar API v3 · PyTorch + Transformers *(opsiyonel)*

**Frontend:** Vanilla HTML/CSS/JS · Web Speech API · Google Cloud TTS · Canvas API · Inter + JetBrains Mono (Google Fonts)

---

## 🚀 Kurulum

### Ön Gereksinimler

- Python 3.10+
- Google Cloud Console hesabı (Calendar API + TTS API)
- Gemini API Key → [Google AI Studio](https://aistudio.google.com/apikey)
- Google Chrome (Web Speech API desteği için)

### Adımlar

```bash
# 1. Klonla
git clone https://github.com/BerkayBilgenn/Otonom.git
cd Otonom

# 2. Sanal ortam
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Bağımlılıklar
pip install -r requirements.txt

# 4. Ortam değişkeni
echo GEMINI_API_KEY=your_key_here > .env

# 5. Google Calendar API
#    - console.cloud.google.com → Calendar API etkinleştir
#    - OAuth 2.0 Client ID oluştur (Desktop App)
#    - JSON'u backend/credentials.json olarak kaydet

# 6. Başlat
python main.py
# → http://localhost:8000
```

> **Not:** İlk çalıştırmada Google OAuth ekranı açılacak — hesabınızla giriş yapıp takvim izni verin.

---

## 🔌 API

### `POST /api/chat`

```json
// Request
{ "message": "Yarın müsait saatleri göster" }

// Response
{ "response": "Yarın için müsait saatler: 09:00, 10:00, 11:00..." }
```

### `GET /api/appointments`

```json
// Response
{
  "appointments": [
    {
      "id": "abc123",
      "title": "Kayıt Randevusu",
      "start": "2026-04-10T14:00:00+03:00",
      "end": "2026-04-10T15:00:00+03:00",
      "status": "confirmed",
      "link": "https://www.google.com/calendar/event?eid=..."
    }
  ]
}
```

---

## 📂 Proje Yapısı

```
Otonom/
├── backend/
│   ├── main.py                      # FastAPI uygulama & endpointler
│   ├── gemini_service.py            # Gemini AI + function calling
│   ├── calendar_service.py          # Google Calendar API (CRUD)
│   ├── prompt_enhancer_service.py   # Hunyuan 7B prompt enhancer
│   ├── download_model.py            # Model indirme scripti
│   ├── requirements.txt             # Python bağımlılıkları
│   ├── .env                         # 🔒 API anahtarları (git dışı)
│   ├── credentials.json             # 🔒 OAuth kimlik bilgileri (git dışı)
│   └── token.json                   # 🔒 OAuth token (git dışı)
│
├── frontend/
│   ├── index.html                   # Ana sayfa
│   ├── app.js                       # STT, TTS, API, UI mantığı
│   └── style.css                    # Dark theme + animasyonlar
│
├── .gitignore
└── README.md
```

---

## 🔒 Güvenlik

Aşağıdaki dosyalar `.gitignore` tarafından korunmaktadır:

| Dosya | İçerik |
|:---|:---|
| `backend/.env` | Gemini API anahtarı |
| `backend/credentials.json` | Google OAuth istemci bilgileri |
| `backend/token.json` | Google OAuth erişim token'ı |
| `backend/models/` | AI model dosyaları |

---

## 📄 Lisans

MIT License — Detaylar için [LICENSE](LICENSE) dosyasına bakın.
