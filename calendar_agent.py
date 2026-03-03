# ===================================================
# calendar_agent.py — Google Calendar İşlemleri
# ===================================================
# Bu modül Google Calendar üzerinde etkinlik listeleme,
# yeni etkinlik ekleme ve etkinlik silme işlemlerini
# gerçekleştirir.
# ===================================================

from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table

console = Console()


def list_upcoming_events(service, max_results: int = 10) -> str:
    """
    Yaklaşan takvim etkinliklerini listeler.

    Args:
        service: Google Calendar API servisi.
        max_results: Gösterilecek maksimum etkinlik sayısı.

    Returns:
        str: Etkinlik listesi.
    """
    try:
        now = datetime.utcnow().isoformat() + "Z"  # UTC zaman damgası

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            return "Yaklaşan etkinlik bulunamadı."

        # Zengin tablo ile göster
        table = Table(title="📅 Yaklaşan Etkinlikler", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Etkinlik", style="cyan", min_width=25)
        table.add_column("Başlangıç", style="green", width=20)
        table.add_column("Bitiş", style="yellow", width=20)
        table.add_column("Konum", style="magenta", width=20)

        lines = []
        for i, event in enumerate(events, 1):
            summary = event.get("summary", "Başlıksız")
            start = event["start"].get("dateTime", event["start"].get("date", "?"))
            end = event["end"].get("dateTime", event["end"].get("date", "?"))
            location = event.get("location", "—")

            # Tarih formatını düzenle
            start_display = start[:16].replace("T", " ") if "T" in start else start
            end_display = end[:16].replace("T", " ") if "T" in end else end

            table.add_row(str(i), summary, start_display, end_display, location)
            lines.append(f"{i}. {summary} — {start_display}")

        console.print(table)
        return "\n".join(lines)

    except Exception as e:
        error_msg = f"Takvim etkinlikleri listelenirken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def create_event(
    service,
    summary: str,
    start_datetime: str,
    end_datetime: str = None,
    description: str = "",
    location: str = "",
    timezone: str = "Europe/Istanbul",
) -> str:
    """
    Google Calendar'a yeni bir etkinlik ekler.

    Args:
        service: Google Calendar API servisi.
        summary: Etkinlik başlığı.
        start_datetime: Başlangıç zamanı (ISO 8601: "2026-03-15T10:00:00").
        end_datetime: Bitiş zamanı (None ise başlangıçtan 1 saat sonra).
        description: Etkinlik açıklaması (opsiyonel).
        location: Etkinlik konumu (opsiyonel).
        timezone: Saat dilimi (varsayılan: Europe/Istanbul).

    Returns:
        str: Oluşturma sonucu mesajı.
    """
    try:
        # Bitiş zamanı belirtilmemişse +1 saat ekle
        if not end_datetime:
            start_dt = datetime.fromisoformat(start_datetime)
            end_dt = start_dt + timedelta(hours=1)
            end_datetime = end_dt.isoformat()

        event_body = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_datetime,
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": timezone,
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 30},  # 30 dk önce bildirim
                ],
            },
        }

        event = (
            service.events()
            .insert(calendarId="primary", body=event_body)
            .execute()
        )

        event_link = event.get("htmlLink", "")
        success_msg = (
            f"Etkinlik oluşturuldu!\n"
            f"  📌 Başlık    : {summary}\n"
            f"  🕐 Başlangıç : {start_datetime}\n"
            f"  🕐 Bitiş     : {end_datetime}\n"
            f"  📍 Konum     : {location or '—'}\n"
            f"  🔗 Link      : {event_link}"
        )
        console.print(f"[green]✓ Etkinlik oluşturuldu: '{summary}'[/green]")
        return success_msg

    except Exception as e:
        error_msg = f"Etkinlik oluşturulurken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def delete_event(service, event_id: str) -> str:
    """
    Belirtilen takvim etkinliğini siler.

    Args:
        service: Google Calendar API servisi.
        event_id: Silinecek etkinliğin ID'si.

    Returns:
        str: Silme sonucu mesajı.
    """
    try:
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        success_msg = f"Etkinlik silindi (ID: {event_id})."
        console.print(f"[green]✓ {success_msg}[/green]")
        return success_msg

    except Exception as e:
        error_msg = f"Etkinlik silinirken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def search_events(service, query: str, max_results: int = 10) -> str:
    """
    Takvimde etkinlik arar.

    Args:
        service: Google Calendar API servisi.
        query: Arama sorgusu.
        max_results: Maksimum sonuç sayısı.

    Returns:
        str: Arama sonuçları.
    """
    try:
        now = datetime.utcnow().isoformat() + "Z"
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
                q=query,
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            return f"'{query}' ile eşleşen etkinlik bulunamadı."

        lines = []
        for i, event in enumerate(events, 1):
            summary = event.get("summary", "Başlıksız")
            start = event["start"].get("dateTime", event["start"].get("date", "?"))
            start_display = start[:16].replace("T", " ") if "T" in start else start
            lines.append(f"{i}. {summary} — {start_display} (ID: {event['id']})")

        result = "\n".join(lines)
        console.print(result)
        return result

    except Exception as e:
        error_msg = f"Etkinlik araması sırasında hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg
