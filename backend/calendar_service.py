"""
Google Calendar API Service
----------------------------
Çağrı merkezi asistanı için takvim işlemleri.
Boşluk kontrolü, boş saat bulma ve randevu oluşturma.
"""

import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")


def get_calendar_service():
    """Google Calendar API istemcisini olusturur."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service


def check_calendar_availability(date: str, time: str) -> dict:
    """
    Belirtilen tarih ve saatte takvimde bosluk olup olmadigini kontrol eder.

    Args:
        date: Tarih (YYYY-MM-DD)
        time: Saat (HH:MM)

    Returns:
        dict: {"available": True/False, "message": "..."}
    """
    try:
        service = get_calendar_service()

        start_str = f"{date}T{time}:00"
        start_dt = datetime.datetime.fromisoformat(start_str)
        end_dt = start_dt + datetime.timedelta(hours=1)

        timezone = "Europe/Istanbul"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_dt.isoformat() + "+03:00",
            timeMax=end_dt.isoformat() + "+03:00",
            singleEvents=True,
            orderBy="startTime",
            timeZone=timezone,
        ).execute()

        events = events_result.get("items", [])

        if not events:
            return {
                "available": True,
                "message": f"{date} tarihinde saat {time} musait."
            }
        else:
            event_names = ", ".join([e.get("summary", "Randevu") for e in events])
            return {
                "available": False,
                "message": f"{date} tarihinde saat {time} dolu. Mevcut randevular: {event_names}"
            }

    except Exception as e:
        return {
            "available": False,
            "message": f"Takvim kontrol edilirken bir hata olustu: {str(e)}"
        }


def get_available_slots(date: str) -> dict:
    """
    Belirtilen tarihteki bos saat araliglarini bulur.
    Sabah 09:00 - Aksam 21:00 arasindaki bos 1 saatlik dilimleri dondurur.

    Args:
        date: Tarih (YYYY-MM-DD)

    Returns:
        dict: {"date": "...", "available_slots": ["09:00", "10:00", ...], "busy_slots": ["14:00", ...]}
    """
    try:
        service = get_calendar_service()
        timezone = "Europe/Istanbul"

        # Gun baslangici ve sonu (09:00 - 21:00)
        day_start = datetime.datetime.fromisoformat(f"{date}T09:00:00")
        day_end = datetime.datetime.fromisoformat(f"{date}T21:00:00")

        # O gundeki tum etkinlikleri al
        events_result = service.events().list(
            calendarId="primary",
            timeMin=day_start.isoformat() + "+03:00",
            timeMax=day_end.isoformat() + "+03:00",
            singleEvents=True,
            orderBy="startTime",
            timeZone=timezone,
        ).execute()

        events = events_result.get("items", [])

        # Dolu saatleri bul
        busy_times = set()
        for event in events:
            start = event.get("start", {})
            start_time = start.get("dateTime", "")
            if start_time:
                # +03:00 kismini ayikla
                event_dt = datetime.datetime.fromisoformat(start_time)
                event_hour = event_dt.hour
                # Etkinligin kapsadigi tum saat dilimlerini isaretle
                end = event.get("end", {})
                end_time = end.get("dateTime", "")
                if end_time:
                    end_dt = datetime.datetime.fromisoformat(end_time)
                    current = event_dt
                    while current < end_dt:
                        busy_times.add(f"{current.hour:02d}:00")
                        current += datetime.timedelta(hours=1)

        # Bos ve dolu saatleri ayir
        all_slots = [f"{h:02d}:00" for h in range(9, 21)]
        available_slots = [s for s in all_slots if s not in busy_times]
        busy_slots = [s for s in all_slots if s in busy_times]

        if available_slots:
            return {
                "date": date,
                "available_slots": available_slots,
                "busy_slots": busy_slots,
                "message": f"{date} tarihinde musait saatler: {', '.join(available_slots)}"
            }
        else:
            return {
                "date": date,
                "available_slots": [],
                "busy_slots": busy_slots,
                "message": f"{date} tarihinde ne yazik ki musait saat bulunmamaktadir."
            }

    except Exception as e:
        return {
            "date": date,
            "available_slots": [],
            "busy_slots": [],
            "message": f"Takvim kontrol edilirken hata olustu: {str(e)}"
        }


def book_appointment(date: str, time: str, appointment_type: str) -> dict:
    """
    Belirtilen tarih ve saatte randevu olusturur. Olusturmadan once saatin bos oldugundan emin olur.
    """
    try:
        # ONCE KONTROL ET
        avail_check = check_calendar_availability(date, time)
        if not avail_check.get("available", True):
            return {
                "success": False,
                "message": f"Uzgunum, {date} saat {time} su anda dolu. Baska bir bosta mi kontrol edebiliriz?",
                "event_link": ""
            }

        service = get_calendar_service()

        start_str = f"{date}T{time}:00"
        start_dt = datetime.datetime.fromisoformat(start_str)
        end_dt = start_dt + datetime.timedelta(hours=1)

        timezone = "Europe/Istanbul"

        event = {
            "summary": f"{appointment_type}",
            "description": f"AI Randevu Asistani tarafindan olusturuldu.\nRandevu Turu: {appointment_type}",
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": timezone,
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 30},
                ],
            },
        }

        created_event = service.events().insert(calendarId="primary", body=event).execute()
        event_link = created_event.get("htmlLink", "")

        return {
            "success": True,
            "message": f"{date} tarihinde saat {time}'da '{appointment_type}' randevunuz basariyla olusturuldu!",
            "event_link": event_link
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Randevu olusturulurken bir hata olustu: {str(e)}",
            "event_link": ""
        }

def cancel_appointment(date: str, time: str) -> dict:
    """
    Belirtilen tarih ve saatteki randevuyu bulup iptal eder (siler).
    """
    try:
        service = get_calendar_service()

        start_str = f"{date}T{time}:00"
        start_dt = datetime.datetime.fromisoformat(start_str)
        end_dt = start_dt + datetime.timedelta(hours=1)
        timezone = "Europe/Istanbul"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_dt.isoformat() + "+03:00",
            timeMax=end_dt.isoformat() + "+03:00",
            singleEvents=True,
            orderBy="startTime",
            timeZone=timezone,
        ).execute()

        events = events_result.get("items", [])

        if not events:
            return {
                "success": False,
                "message": f"{date} tarihinde saat {time}'da iptal edilecek bir randevu bulunamadi."
            }

        event_id = events[0]["id"]
        event_name = events[0].get("summary", "Randevu")
        
        service.events().delete(calendarId="primary", eventId=event_id).execute()

        return {
            "success": True,
            "message": f"{date} saat {time}'daki '{event_name}' basariyla iptal edildi."
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Randevu iptal edilirken bir hata olustu: {str(e)}"
        }
