import os
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from rich.console import Console

import config

console = Console()


def authenticate() -> Credentials:
    """
    Google OAuth 2.0 kimlik doğrulamasını gerçekleştirir.

    Akış:
    1. token.json varsa → mevcut token'ı yükle.
    2. Token süresi dolduysa → otomatik yenile.
    3. Token yoksa → tarayıcı ile kullanıcıdan izin al.
    4. Yeni token'ı token.json'a kaydet.

    Returns:
        Credentials: Geçerli Google API kimlik bilgileri.
    """
    creds = None

    if os.path.exists(config.TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(
                config.TOKEN_FILE, config.SCOPES
            )
            console.print("[green]✓[/green] Mevcut token dosyası yüklendi.")
        except Exception as e:
            console.print(f"[yellow]⚠ Token dosyası okunamadı: {e}[/yellow]")
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            console.print("[green]✓[/green] Token başarıyla yenilendi.")
        except Exception as e:
            console.print(f"[yellow]⚠ Token yenilenirken hata: {e}[/yellow]")
            creds = None

    if not creds or not creds.valid:
        if not os.path.exists(config.CREDENTIALS_FILE):
            console.print(
                f"[red]✗ '{config.CREDENTIALS_FILE}' dosyası bulunamadı![/red]\n"
                "  Google Cloud Console'dan OAuth 2.0 istemci kimliğini indirip\n"
                "  proje klasörüne 'credentials.json' olarak kaydedin."
            )
            sys.exit(1)

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CREDENTIALS_FILE, config.SCOPES
            )
            creds = flow.run_local_server(port=0)
            console.print(
                "[green]✓[/green] Kimlik doğrulama başarılı! Token kaydediliyor..."
            )
        except Exception as e:
            console.print(f"[red]✗ Kimlik doğrulama başarısız: {e}[/red]")
            sys.exit(1)

    try:
        with open(config.TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())
        console.print(f"[green]✓[/green] Token '{config.TOKEN_FILE}' dosyasına kaydedildi.")
    except Exception as e:
        console.print(f"[yellow]⚠ Token kaydedilemedi: {e}[/yellow]")

    return creds


def get_service(service_name: str, version: str, creds: Credentials = None):
    """
    Belirtilen Google API servisi için istemci nesnesi oluşturur.

    Args:
        service_name: API adı (ör: "drive", "docs", "sheets", "slides",
                      "calendar", "gmail")
        version:      API sürümü (ör: "v3", "v1", "v4")
        creds:        Google kimlik bilgileri. None ise authenticate() çağrılır.

    Returns:
        googleapiclient.discovery.Resource: API istemci nesnesi.
    """
    if creds is None:
        creds = authenticate()

    try:
        service = build(service_name, version, credentials=creds)
        console.print(
            f"[green]✓[/green] {service_name} ({version}) servisi hazır."
        )
        return service
    except Exception as e:
        console.print(
            f"[red]✗ {service_name} servisi oluşturulamadı: {e}[/red]"
        )
        return None




def get_all_services(creds: Credentials = None) -> dict:
    """
    Tüm Google API servislerini tek seferde başlatır ve bir sözlük döndürür.

    Returns:
        dict: {"drive": ..., "docs": ..., "sheets": ...,
               "slides": ..., "calendar": ..., "gmail": ...}
    """
    if creds is None:
        creds = authenticate()

    services = {
        "drive": get_service("drive", "v3", creds),
        "docs": get_service("docs", "v1", creds),
        "sheets": get_service("sheets", "v4", creds),
        "slides": get_service("slides", "v1", creds),
        "calendar": get_service("calendar", "v3", creds),
        "gmail": get_service("gmail", "v1", creds),
    }
    return services


if __name__ == "__main__":
    console.print(f"\n[bold cyan]{config.APP_NAME} — Kimlik Doğrulama Testi[/bold cyan]\n")
    credentials = authenticate()
    if credentials and credentials.valid:
        console.print("\n[bold green]✓ Kimlik doğrulama başarılı![/bold green]")
        console.print("  Tüm servisler başlatılıyor...\n")
        svcs = get_all_services(credentials)
        for name, svc in svcs.items():
            status = "[green]Hazır[/green]" if svc else "[red]Başarısız[/red]"
            console.print(f"  • {name:>10}: {status}")
    else:
        console.print("\n[bold red]✗ Kimlik doğrulama başarısız.[/bold red]")
