"""
Gemini AI Service - Cagri Merkezi Asistani
"""

import os
import sys
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

api_key = os.getenv("GEMINI_API_KEY")
print(f"[INIT] API Key loaded: {api_key[:8]}..." if api_key else "[INIT] API KEY YOK!")
genai.configure(api_key=api_key)

# ============================================================
# SYSTEM INSTRUCTION — CAGRI MERKEZI ASISTANI
# ============================================================
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")
CURRENT_DAY = datetime.now().strftime("%A")

SYSTEM_INSTRUCTION = f"""Sen profesyonel, nazik ve yardımsever bir çağrı merkezi asistanısın.
Görevin kullanıcıların randevu almasına yardımcı olmaktır.

ÇOK ÖNEMLİ BİLGİ: BUGÜNÜN TARİHİ: {CURRENT_DATE} ({CURRENT_DAY})
Kullanıcı "yarın" derse, bu tarihe tam olarak 1 gün ekle. Asla eski yıllardaki (2024, 2023 vb.) tarihlere randevu verme! Yılı her zaman {CURRENT_DATE[:4]} veya sonrası kullan.

Temel kuralların:
1. Kullanıcı bir saat veya tarih belirttiğinde, MUTLAKA önce takvimi kontrol et (check_calendar_availability).
2. Eğer istenen saat doluysa, o günün tüm müsait saatlerini bul (get_available_slots) ve kullanıcıya alternatif saatler sun.
3. Kullanıcı bir saati onayladığında, randevuyu oluştur (book_appointment).
4. Kullanıcı var olan bir randevusunu iptal etmek isterse, iptal et (cancel_appointment).
5. Her zaman kibar, profesyonel ve çözüm odaklı ol.
6. Konuşmaların kısa ve öz olsun — sesli asistan formatına uygun olmalı.
7. Kullanıcıya "Siz" diye hitap et, resmi ama samimi bir ton kullan.

Örnek akış:
- Kullanıcı: "Yarın saat 20:00'de kayıt olmak istiyorum"
- Sen: Önce check_calendar_availability ile 20:00'ı kontrol et
- Eğer doluysa: get_available_slots ile o günün boş saatlerini bul ve sun
Eğer boşsa: Onay al ve book_appointment ile randevuyu oluştur

Bugünün tarihi bilgini kullan. "yarın" = bugün + 1 gün, "bugün" = bugünün tarihi.
Tarih formatı: YYYY-MM-DD, Saat formatı: HH:MM.
Türkçe konuş.
Ayrıca, kullanıcı görsel oluşturmak için bir prompt isterse veya "bana ... resmi için bir prompt hazırla" derse, 'enhance_image_prompt' aracını çağırıp cevabı o dönen kelimelerle zenginleştirerek ver."""

# ============================================================
# TOOL DECLARATIONS
# ============================================================
tools = [
    {
        "function_declarations": [
            {
                "name": "check_calendar_availability",
                "description": "Belirtilen tarih ve saatte takvimde bosluk olup olmadigini kontrol eder. Kullanici belirli bir saatte randevu almak istediginde bu fonksiyonu cagir.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Tarih YYYY-MM-DD formatinda. Ornek: 2026-04-10"},
                        "time": {"type": "string", "description": "Saat HH:MM formatinda. Ornek: 18:00"},
                    },
                    "required": ["date", "time"],
                },
            },
            {
                "name": "get_available_slots",
                "description": "Belirtilen tarihteki tum musait (bos) saat araliglarini getirir. Kullaniciya alternatif saatler sunmak istediginde veya kullanici hangi saatlerin bos oldugunu sordugunda bu fonksiyonu cagir.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Tarih YYYY-MM-DD formatinda. Ornek: 2026-04-10"},
                    },
                    "required": ["date"],
                },
            },
            {
                "name": "book_appointment",
                "description": "Belirtilen tarih ve saatte 1 saatlik bir randevu olusturur. Kullanici bir saati onayladiktan sonra bu fonksiyonu cagir.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Randevu tarihi YYYY-MM-DD formatinda."},
                        "time": {"type": "string", "description": "Randevu saati HH:MM formatinda."},
                        "appointment_type": {"type": "string", "description": "Randevu turu. Ornek: Kayit, Gorusme, Danismanlik, Genel Randevu"},
                    },
                    "required": ["date", "time", "appointment_type"],
                },
            },
            {
                "name": "cancel_appointment",
                "description": "Kullanici var olan bir randevusunu veya toplantisini iptal etmek istedigini soylediginde bunu kullan. İptal edilecek tam tarih ve saati icermelidir.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "İptal edilecek randevunun tarihi YYYY-MM-DD formatinda."},
                        "time": {"type": "string", "description": "İptal edilecek randevunun saati HH:MM formatinda."},
                    },
                    "required": ["date", "time"],
                },
            },
            {
                "name": "enhance_image_prompt",
                "description": "Kullanicinin bir gorsel (resim) olusturmak amaciyla verdigi basit, kisa fikirleri alip son derece kaliteli bir gorsel prompt'a donusturur. Gorsel prompt talebi gelirse mutlaka kullan.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "base_prompt": {"type": "string", "description": "Kullanicinin verdigi basit resim veya prompt fikri. Ornek: Karda kosan atlar."},
                    },
                    "required": ["base_prompt"],
                },
            },
        ]
    }
]

# ============================================================
# MODEL & CHAT
# ============================================================
print("[INIT] Creating Gemini model (gemini-2.5-flash)...")
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_INSTRUCTION,
    tools=tools,
)
chat_session = model.start_chat(history=[])
print("[INIT] Gemini model ready!")

# ============================================================
# FUNCTION MAP
# ============================================================
from calendar_service import check_calendar_availability, get_available_slots, book_appointment, cancel_appointment
from prompt_enhancer_service import enhance_image_prompt

AVAILABLE_FUNCTIONS = {
    "check_calendar_availability": check_calendar_availability,
    "get_available_slots": get_available_slots,
    "book_appointment": book_appointment,
    "cancel_appointment": cancel_appointment,
    "enhance_image_prompt": enhance_image_prompt,
}


# ============================================================
# PROCESS MESSAGE
# ============================================================
async def process_message(user_message: str) -> str:
    try:
        print(f"[GEMINI] Sending message: {user_message}")
        response = chat_session.send_message(user_message)
        print(f"[GEMINI] Got response, checking for function calls...")

        while True:
            part = response.candidates[0].content.parts[0]

            fc = part.function_call
            if not fc or not fc.name:
                break

            function_name = fc.name
            function_args = dict(fc.args)
            print(f"[TOOL CALL]: {function_name}({function_args})")

            if function_name in AVAILABLE_FUNCTIONS:
                result = AVAILABLE_FUNCTIONS[function_name](**function_args)
            else:
                result = {"error": f"Unknown function: {function_name}"}

            print(f"[TOOL RESULT]: {result}")

            response = chat_session.send_message(
                genai.protos.Content(
                    parts=[
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=function_name,
                                response={"result": json.dumps(result, ensure_ascii=False)},
                            )
                        )
                    ]
                )
            )

        final_text = response.text
        print(f"[GEMINI] Final response: {final_text[:100]}...")
        return final_text

    except Exception as e:
        import traceback
        error = traceback.format_exc()
        print(f"[GEMINI ERROR]:\n{error}")
        return f"Ozur dileriz, bir teknik sorun olustu: {str(e)}"
