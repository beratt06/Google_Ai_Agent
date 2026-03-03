# ===================================================
# voice_handler.py — Ses Tanıma (Speech-to-Text)
# ===================================================
# Bu modül, kullanıcının mikrofon aracılığıyla verdiği
# sesli komutları metne çevirir. Google Speech Recognition
# API'sini kullanır.
# ===================================================

import speech_recognition as sr
from rich.console import Console

import config

console = Console()

# Global recognizer nesnesi
recognizer = sr.Recognizer()


def listen_from_microphone(language: str = None, timeout: int = 10) -> str | None:
    """
    Mikrofondan ses dinler ve metne çevirir.

    Args:
        language: Tanıma dili (ör: "tr-TR", "en-US").
                  None ise config'deki varsayılan kullanılır.
        timeout: Ses bekleme süresi (saniye).

    Returns:
        str | None: Tanınan metin veya hata durumunda None.
    """
    lang = language or config.SPEECH_LANGUAGE

    try:
        with sr.Microphone() as source:
            console.print("\n[bold cyan]🎤 Dinliyorum... (konuşmaya başlayın)[/bold cyan]")

            # Ortam gürültüsünü kalibre et (1 saniyelik örneklem)
            recognizer.adjust_for_ambient_noise(source, duration=1)

            # Sesi dinle
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=30)
            console.print("[yellow]⟳ Ses tanınıyor...[/yellow]")

        # Google Speech Recognition ile metne çevir
        text = recognizer.recognize_google(audio, language=lang)
        console.print(f"[green]✓ Tanınan metin:[/green] {text}")
        return text

    except sr.WaitTimeoutError:
        console.print("[yellow]⚠ Zaman aşımı — ses algılanamadı.[/yellow]")
        return None

    except sr.UnknownValueError:
        console.print("[yellow]⚠ Ses anlaşılamadı. Lütfen tekrar deneyin.[/yellow]")
        return None

    except sr.RequestError as e:
        console.print(
            f"[red]✗ Ses tanıma servisi hatası: {e}[/red]\n"
            "  İnternet bağlantınızı kontrol edin."
        )
        return None

    except OSError:
        console.print(
            "[red]✗ Mikrofon bulunamadı![/red]\n"
            "  PyAudio kurulu mu? → pip install PyAudio\n"
            "  Mikrofon bağlı mı ve izinler verildi mi?"
        )
        return None

    except Exception as e:
        console.print(f"[red]✗ Beklenmeyen ses tanıma hatası: {e}[/red]")
        return None


def check_microphone() -> bool:
    """
    Sistemde kullanılabilir mikrofon olup olmadığını kontrol eder.

    Returns:
        bool: Mikrofon varsa True, yoksa False.
    """
    try:
        mic_list = sr.Microphone.list_microphone_names()
        if mic_list:
            console.print(f"[green]✓ {len(mic_list)} mikrofon bulundu:[/green]")
            for i, name in enumerate(mic_list[:5]):  # İlk 5'i göster
                console.print(f"  {i}. {name}")
            if len(mic_list) > 5:
                console.print(f"  ... ve {len(mic_list) - 5} tane daha.")
            return True
        else:
            console.print("[yellow]⚠ Kullanılabilir mikrofon bulunamadı.[/yellow]")
            return False
    except Exception as e:
        console.print(f"[red]✗ Mikrofon kontrol hatası: {e}[/red]")
        return False


def get_input(prompt_text: str = "Komutunuz") -> str | None:
    """
    Kullanıcıdan ses veya metin girişi alır.
    Kullanıcı girdi modunu (ses/metin) seçebilir.

    Args:
        prompt_text: Komut istemi metni.

    Returns:
        str | None: Kullanıcının komutu veya None (çıkış/hata).
    """
    console.print(
        f"\n[bold]{prompt_text}[/bold] "
        "[dim](yazın veya 's' ile sesli komut verin, 'q' çıkış)[/dim]"
    )
    user_input = input(">>> ").strip()

    if not user_input:
        return None

    # Çıkış komutları
    if user_input.lower() in ("q", "quit", "exit", "çık", "çıkış"):
        return "EXIT"

    # Ses modu
    if user_input.lower() in ("s", "ses", "voice", "dinle"):
        return listen_from_microphone()

    # Metin modu — girdiyi doğrudan döndür
    return user_input


# -------------------- Doğrudan Test --------------------
if __name__ == "__main__":
    console.print(f"\n[bold cyan]{config.APP_NAME} — Ses Tanıma Testi[/bold cyan]\n")

    # Mikrofon kontrolü
    has_mic = check_microphone()

    if has_mic:
        console.print("\n[cyan]Sesli komut testi başlatılıyor...[/cyan]")
        result = listen_from_microphone()
        if result:
            console.print(f"\n[bold green]Sonuç: {result}[/bold green]")
    else:
        console.print("[yellow]Mikrofon yok — metin modu kullanılacak.[/yellow]")
        text = input("Test metni girin: ")
        console.print(f"Girdiniz: {text}")
