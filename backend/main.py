"""
AI Voice Fitness Coach - FastAPI Backend
"""

import sys
import traceback

# Windows konsol encoding fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import os

# ============================================================
# FASTAPI UYGULAMASI
# ============================================================
app = FastAPI(title="AI Voice Fitness Coach")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# FRONTEND DOSYALARINI SUNMA
# ============================================================
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")


@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/app.js")
async def serve_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.js"), media_type="application/javascript")


@app.get("/style.css")
async def serve_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "style.css"), media_type="text/css")


# ============================================================
# VERI MODELLERİ
# ============================================================
class ChatRequest(BaseModel):
    message: str


# ============================================================
# API UÇ NOKTASI — DETAYLI HATA YAKALAMA
# ============================================================
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        print(f"\n[USER]: {request.message}")

        # Lazy import - hata detayli gorunsun
        from gemini_service import process_message

        ai_response = await process_message(request.message)

        print(f"[AI]: {ai_response}")

        return JSONResponse(content={"response": ai_response})

    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"\n[CRITICAL ERROR]:\n{error_detail}")
        # Hatayı frontend'e de döndür ki görelim
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "traceback": error_detail}
        )


# ============================================================
# TAKVİM RANDEVULARI ENDPOINT
# ============================================================
@app.get("/api/appointments")
async def get_appointments():
    """Yaklaşan randevuları Google Calendar'dan çeker."""
    try:
        import datetime
        from calendar_service import get_calendar_service

        service = get_calendar_service()
        timezone = "Europe/Istanbul"

        # Bugünden itibaren 30 günlük randevuları getir
        now = datetime.datetime.now()
        time_min = now.isoformat() + "+03:00"
        time_max = (now + datetime.timedelta(days=30)).isoformat() + "+03:00"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            timeZone=timezone,
            maxResults=50,
        ).execute()

        events = events_result.get("items", [])

        appointments = []
        for event in events:
            start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", ""))
            end = event.get("end", {}).get("dateTime", event.get("end", {}).get("date", ""))
            appointments.append({
                "id": event.get("id", ""),
                "title": event.get("summary", "Randevu"),
                "description": event.get("description", ""),
                "start": start,
                "end": end,
                "status": event.get("status", "confirmed"),
                "link": event.get("htmlLink", ""),
            })

        return JSONResponse(content={"appointments": appointments})

    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"\n[CALENDAR ERROR]:\n{error_detail}")
        # 200 döndür ama hata mesajını da gönder — frontend güzelce göstersin
        return JSONResponse(
            status_code=200,
            content={
                "appointments": [],
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    print("[START] AI Voice Fitness Coach Sunucusu Baslatiliyor...")
    print("http://localhost:8000 adresinden erisebilirsiniz.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
