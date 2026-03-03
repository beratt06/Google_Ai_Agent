# ===================================================
# main.py — Ana Uygulama Döngüsü
# ===================================================
# Google AI Asistan'ın giriş noktası.
# Kullanıcıdan ses veya metin girişi alır, LLM ile
# niyeti analiz eder ve ilgili Google servisini çağırır.
# ===================================================

import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

import config
from auth_google import authenticate, get_all_services
from voice_handler import get_input
from llm_router import analyze_intent, get_chat_response

# ---- Agent modülleri ----
import drive_agent
import docs_agent
import sheets_agent
import slides_agent
import calendar_agent
import gmail_agent

console = Console()


# ================================================================
# Servis Yönlendirme Haritası
# ================================================================
# Her (service, action) çifti → çağrılacak fonksiyon ve
# Google API servis anahtarı eşlemesi.
# ================================================================

ACTION_MAP = {
    # --- Google Drive ---
    ("drive", "list_files"): {
        "func": drive_agent.list_files,
        "svc_key": "drive",
    },
    ("drive", "search_files"): {
        "func": drive_agent.search_files,
        "svc_key": "drive",
    },
    ("drive", "download_file"): {
        "func": drive_agent.download_file,
        "svc_key": "drive",
    },
    ("drive", "get_file_info"): {
        "func": drive_agent.get_file_info,
        "svc_key": "drive",
    },
    # --- Google Docs ---
    ("docs", "read_document"): {
        "func": docs_agent.read_document,
        "svc_key": "docs",
    },
    ("docs", "create_document"): {
        "func": docs_agent.create_document,
        "svc_key": "docs",
    },
    ("docs", "create_professional_document"): {
        "func": docs_agent.create_professional_document,
        "svc_key": "docs",
    },
    ("docs", "append_to_document"): {
        "func": docs_agent.append_to_document,
        "svc_key": "docs",
    },
    # --- Google Sheets ---
    ("sheets", "read_sheet"): {
        "func": sheets_agent.read_sheet,
        "svc_key": "sheets",
    },
    ("sheets", "write_to_sheet"): {
        "func": sheets_agent.write_to_sheet,
        "svc_key": "sheets",
    },
    ("sheets", "append_to_sheet"): {
        "func": sheets_agent.append_to_sheet,
        "svc_key": "sheets",
    },
    ("sheets", "create_spreadsheet"): {
        "func": sheets_agent.create_spreadsheet,
        "svc_key": "sheets",
    },
    # --- Google Slides ---
    ("slides", "read_presentation"): {
        "func": slides_agent.read_presentation,
        "svc_key": "slides",
    },
    ("slides", "create_presentation"): {
        "func": slides_agent.create_presentation,
        "svc_key": "slides",
    },
    ("slides", "create_full_presentation"): {
        "func": slides_agent.create_full_presentation,
        "svc_key": "slides",
    },
    ("slides", "add_slide_with_text"): {
        "func": slides_agent.add_slide_with_text,
        "svc_key": "slides",
    },
    # --- Google Calendar ---
    ("calendar", "list_upcoming_events"): {
        "func": calendar_agent.list_upcoming_events,
        "svc_key": "calendar",
    },
    ("calendar", "create_event"): {
        "func": calendar_agent.create_event,
        "svc_key": "calendar",
    },
    ("calendar", "delete_event"): {
        "func": calendar_agent.delete_event,
        "svc_key": "calendar",
    },
    ("calendar", "search_events"): {
        "func": calendar_agent.search_events,
        "svc_key": "calendar",
    },
    # --- Gmail ---
    ("gmail", "send_email"): {
        "func": gmail_agent.send_email,
        "svc_key": "gmail",
    },
    ("gmail", "create_draft"): {
        "func": gmail_agent.create_draft,
        "svc_key": "gmail",
    },
    ("gmail", "list_messages"): {
        "func": gmail_agent.list_messages,
        "svc_key": "gmail",
    },
    ("gmail", "read_message"): {
        "func": gmail_agent.read_message,
        "svc_key": "gmail",
    },
}


# ================================================================
# Komut Yürütücü
# ================================================================

def execute_command(intent: dict, services: dict) -> str:
    """
    LLM tarafından üretilen niyet nesnesini alır ve
    ilgili agent fonksiyonunu çalıştırır.

    Args:
        intent: {"service", "action", "params", "explanation"} sözlüğü.
        services: get_all_services() ile alınan servis nesneleri.

    Returns:
        str: İşlem sonucu mesajı.
    """
    service_name = intent.get("service", "")
    action = intent.get("action", "")
    params = intent.get("params", {})
    explanation = intent.get("explanation", "")

    # Kullanıcıya açıklamayı göster
    if explanation:
        console.print(f"\n[bold yellow]💡 {explanation}[/bold yellow]")

    # Genel sohbet — Google servisi gerektirmeyen yanıt
    if service_name == "chat":
        message = params.get("message", explanation or "Bir şey söyleyemedim.")
        return message

    # Eylem haritasında bul
    map_key = (service_name, action)
    if map_key not in ACTION_MAP:
        return (
            f"Üzgünüm, '{service_name}.{action}' eylemi henüz desteklenmiyor.\n"
            f"Desteklenen servisler: drive, docs, sheets, slides, calendar, gmail"
        )

    action_info = ACTION_MAP[map_key]
    func = action_info["func"]
    svc_key = action_info["svc_key"]

    # İlgili Google API servisi
    api_service = services.get(svc_key)
    if api_service is None:
        return f"'{svc_key}' servisi başlatılamadı. Lütfen kimlik doğrulamasını kontrol edin."

    # Fonksiyonu çağır — service parametresini ekleyerek
    try:
        result = func(api_service, **params)
        return result
    except TypeError as e:
        # Eksik/fazla parametre hatası
        return (
            f"Parametre hatası: {e}\n"
            f"Lütfen komutunuzu daha ayrıntılı verin.\n"
            f"Beklenen parametreler: {func.__code__.co_varnames[:func.__code__.co_argcount]}"
        )
    except Exception as e:
        return f"İşlem sırasında beklenmeyen hata: {e}"


# ================================================================
# Hoş Geldin Ekranı
# ================================================================

def show_welcome():
    """Uygulama başlangıç ekranını gösterir."""
    welcome_text = Text()
    welcome_text.append(f"  {config.APP_NAME}  ", style="bold white on blue")
    welcome_text.append(f"  v{config.APP_VERSION}", style="dim")

    panel = Panel(
        "[cyan]Google ekosistemi ile tam entegre kişisel AI asistanınız.[/cyan]\n\n"
        "[bold]Kullanım:[/bold]\n"
        "  • Komutunuzu yazın ve Enter'a basın\n"
        "  • Sesli komut için [bold]'s'[/bold] yazın\n"
        "  • Çıkmak için [bold]'q'[/bold] yazın\n\n"
        "[bold]Örnek komutlar:[/bold]\n"
        '  • "Drive\'daki dosyalarımı listele"\n'
        '  • "Yarın saat 14\'te toplantı ekle"\n'
        '  • "ali@mail.com\'a proje raporu gönder"\n'
        '  • "Yeni bir Google Docs oluştur"\n'
        '  • "Takvimimdeki etkinlikleri göster"\n'
        '  • "Gmail gelen kutumu göster"',
        title=welcome_text,
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)


# ================================================================
# Ana Döngü
# ================================================================

def main():
    """Uygulama ana giriş noktası."""
    show_welcome()

    # --- Adım 1: Google Kimlik Doğrulama ---
    console.print("\n[bold]1. Google Hesabına Bağlanılıyor...[/bold]")
    try:
        creds = authenticate()
    except Exception as e:
        console.print(f"[red]✗ Kimlik doğrulama başarısız: {e}[/red]")
        sys.exit(1)

    # --- Adım 2: Tüm Servisleri Başlat ---
    console.print("\n[bold]2. Google Servisleri Başlatılıyor...[/bold]")
    services = get_all_services(creds)

    active_services = sum(1 for s in services.values() if s is not None)
    console.print(
        f"\n[green]✓ {active_services}/{len(services)} servis aktif.[/green]"
    )

    # --- Adım 3: Ollama (Lokal LLM) Kontrolü ---
    console.print(f"\n[bold]3. LLM:[/bold] Ollama (Lokal) — {config.OLLAMA_MODEL}")
    console.print(f"   Sunucu: {config.OLLAMA_BASE_URL}")
    try:
        import httpx
        resp = httpx.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            console.print(f"[green]✓ Ollama çalışıyor. Yüklü modeller: {', '.join(models) or 'yok'}[/green]")
            if not any(config.OLLAMA_MODEL in m for m in models):
                console.print(
                    f"[yellow]⚠ '{config.OLLAMA_MODEL}' modeli yüklü değil! "
                    f"Çalıştırın: ollama pull {config.OLLAMA_MODEL}[/yellow]"
                )
        else:
            console.print("[yellow]⚠ Ollama yanıt verdi ama beklenmeyen durum kodu.[/yellow]")
    except Exception:
        console.print(
            "[red]⚠ Ollama'ya bağlanılamadı! Çalıştırın: ollama serve[/red]"
        )

    console.print("\n" + "═" * 60)
    console.print("[bold green]Asistan hazır! Komutlarınızı bekliyorum...[/bold green]")
    console.print("═" * 60)

    # --- Ana Komut Döngüsü ---
    while True:
        try:
            # Kullanıcıdan girdi al (ses veya metin)
            user_input = get_input("Komutunuz")

            # Giriş kontrolü
            if user_input is None:
                continue
            if user_input == "EXIT":
                console.print("\n[bold blue]👋 Güle güle! İyi günler.[/bold blue]\n")
                break

            # Özel komutlar
            if user_input.lower() in ("help", "yardım"):
                show_welcome()
                continue

            # LLM ile niyet analizi
            intent = analyze_intent(user_input)

            if intent is None:
                console.print(
                    "[yellow]⚠ Komutunuz anlaşılamadı. Lütfen tekrar deneyin.[/yellow]"
                )
                continue

            # Komutu yürüt
            result = execute_command(intent, services)

            # Sonucu göster
            console.print(f"\n[bold]📋 Sonuç:[/bold]")
            console.print(result)

        except KeyboardInterrupt:
            console.print("\n\n[bold blue]👋 Program sonlandırıldı.[/bold blue]\n")
            break
        except Exception as e:
            console.print(f"\n[red]✗ Beklenmeyen hata: {e}[/red]")
            console.print("[dim]Komut döngüsü devam ediyor...[/dim]")
            continue


# -------------------- Giriş Noktası --------------------
if __name__ == "__main__":
    main()
