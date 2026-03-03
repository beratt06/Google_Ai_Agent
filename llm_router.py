# ===================================================
# llm_router.py — LLM Tabanlı Niyet Analizi ve Yönlendirme
# ===================================================
# Bu modül, kullanıcının doğal dilde verdiği komutları
# Ollama (lokal LLM) aracılığıyla analiz eder ve
# uygun Google servisine yönlendirilmek üzere yapılandırılmış
# bir JSON çıktısı üretir.
#
# Ollama, OpenAI-uyumlu bir API sunar (/v1/chat/completions)
# Bu sayede openai Python kütüphanesi ile doğrudan kullanılır.
# ===================================================

import json
from rich.console import Console

import config

console = Console()

# -------------------- Ollama LLM İstemcisi --------------------

def _get_llm_client():
    """
    Ollama'nın OpenAI-uyumlu API'si üzerinden istemci oluşturur.
    Ollama varsayılan olarak http://localhost:11434 adresinde çalışır.

    Returns:
        tuple: (client, model_name, provider) veya hata → (None, None, None).
    """
    try:
        from openai import OpenAI

        # Ollama, OpenAI-uyumlu /v1 endpoint'i sunar
        # API key gerekmez ama kütüphane boş bırakılamaz → "ollama" yazıyoruz
        client = OpenAI(
            base_url=f"{config.OLLAMA_BASE_URL}/v1",
            api_key="ollama",  # Ollama için dummy key yeterli
        )
        console.print(
            f"[green]✓[/green] Ollama bağlantısı hazır "
            f"({config.OLLAMA_BASE_URL} / {config.OLLAMA_MODEL})"
        )
        return client, config.OLLAMA_MODEL, "ollama"

    except Exception as e:
        console.print(f"[red]✗ Ollama istemcisi oluşturulamadı: {e}[/red]")
        console.print(
            "[yellow]  Ollama çalışıyor mu? → ollama serve[/yellow]\n"
            f"[yellow]  Model indirildi mi? → ollama pull {config.OLLAMA_MODEL}[/yellow]"
        )
        return None, None, None


# -------------------- Sistem Promptu --------------------

SYSTEM_PROMPT = """Sen, kullanıcının Google ekosistemi ile etkileşim kurmak için verdiği doğal dil komutlarını analiz eden akıllı bir asistansın.

Görevin: Kullanıcının niyetini anla ve aşağıdaki JSON formatında bir yanıt üret. Yanıtın SADECE geçerli bir JSON nesnesi olmalı, başka hiçbir metin veya açıklama ekleme.

Desteklenen servisler ve eylemleri:

1. **drive** (Google Drive)
   - list_files: Dosyaları listele → {"max_results": 10}
   - search_files: Dosya ara → {"query": "aranacak_kelime"}
   - download_file: Dosya indir → {"file_id": "ID"}
   - get_file_info: Dosya bilgisi → {"file_id": "ID"}

2. **docs** (Google Docs)
   - read_document: Belge oku → {"document_id": "ID"}
   - create_document: Biçimlendirilmiş belge oluştur →
       {"title": "başlık", "body_text": "İÇERİK (Markdown destekli)", "theme": "blue"}
     ÖNEMLİ: body_text'i Markdown sözdizimi ile yaz:
       # Büyük Başlık   → ana başlık
       ## Bölüm Adı    → alt başlık (bold, renkli)
       ### Alt Başlık  → küçük başlık
       * madde veya - madde  → madde işareti listesi
       1. madde → numaralı liste
       Normal satırlar → paragraf metni
     theme seçenekleri: "blue" (varsayılan), "dark"
     Kullanıcı bir konu belirtmişse ASLA kısa ve yüzeysel içerik yazma;
     en az 4-6 bölüm, her bölümde 2-4 paragraf veya madde listesi olsun.
   - create_professional_document: Bölümlere ayrılmış profesyonel belge →
       {"title": "başlık", "sections": [{"heading": "Bölüm Adı", "content": "..."}, ...], "theme": "blue"}
     sections: Her bölümün başlığı ve içeriği ayrı dict olarak belirtilir.
     İçerikte * ile madde işareti kullanılabilir.
   - append_to_document: Belgeye biçimlendirilmiş içerik ekle → {"document_id": "ID", "text": "Markdown metin"}

3. **sheets** (Google Sheets)
   - read_sheet: Tablo oku → {"spreadsheet_id": "ID", "range_name": "A1:Z100"}
   - write_to_sheet: Tabloya yaz → {"spreadsheet_id": "ID", "range_name": "A1", "values": [["a","b"]]}
   - append_to_sheet: Satır ekle → {"spreadsheet_id": "ID", "range_name": "A:D", "values": [["a","b"]]}
   - create_spreadsheet: Tablo oluştur → {"title": "başlık"}

4. **slides** (Google Slides)
   - read_presentation: Sunum oku → {"presentation_id": "ID"}
   - create_full_presentation: TAM PROFESYONEL SUNUM OLUŞTUR (ÖNERİLEN) →
       {
         "title": "Sunum Başlığı",
         "subtitle": "Alt başlık veya tarih",
         "theme": "blue",
         "slides": [
           {"title": "Giriş", "content": "Madde 1\nMadde 2\nMadde 3"},
           {"title": "Bölüm 1", "section": true},
           {"title": "Alt Konu", "content": "Açıklama\nDetaylar\nÖrnekler"},
           {"title": "Sonuç", "content": "Özet\nÖneriler"}
         ]
       }
     KURALLAR:
     - Her "content" satırı ayrı bir madde olarak gösterilir. \n ile ayır.
     - "section": true olan slaytlar renkli bölüm ayırıcısı olur, içerik olmaz.
     - theme: "blue" | "teal" | "dark" | "red"
     - KESİNLİKLE en az 5-8 slayt oluştur; kısa ve eksik sunum yapma.
     - Kullanıcı sunum konusunu söylediyse her slayta gerçek içerik yaz.
   - create_presentation: Boş sunum → {"title": "başlık"}
   - add_slide_with_text: Mevcut sunuma slayt ekle → {"presentation_id": "ID", "title_text": "başlık", "body_text": "içerik", "theme": "blue"}

5. **calendar** (Google Calendar)
   - list_upcoming_events: Etkinlikleri listele → {"max_results": 10}
   - create_event: Etkinlik oluştur → {"summary": "başlık", "start_datetime": "2026-03-15T10:00:00", "end_datetime": "2026-03-15T11:00:00", "description": "", "location": ""}
   - delete_event: Etkinlik sil → {"event_id": "ID"}
   - search_events: Etkinlik ara → {"query": "aranacak"}

6. **gmail** (Gmail)
   - send_email: E-posta gönder → {"to": "alici@mail.com", "subject": "konu", "body": "içerik"}
   - create_draft: Taslak oluştur → {"to": "alici@mail.com", "subject": "konu", "body": "içerik"}
   - list_messages: Mesajları listele → {"max_results": 10, "query": ""}
   - read_message: Mesaj oku → {"message_id": "ID"}

7. **chat** (Sohbet — hiçbir Google servisine yönlendirilmeyecek genel sorular)
   - chat_response: Genel sohbet → {"message": "cevap metni"}

ÇIKTI FORMATI (kesinlikle bu JSON yapısını kullan):
{
    "service": "servis_adı",
    "action": "eylem_adı",
    "params": { ... parametreler ... },
    "explanation": "Kullanıcıya gösterilecek kısa açıklama"
}

ÖNEMLİ KURALLAR:
- Bugünün tarihi: """ + "2026-03-03" + """
- Tarih/saat bilgisi gerektiğinde ISO 8601 formatını kullan (YYYY-MM-DDTHH:MM:SS).
- Kullanıcı "yarın" derse bugünden bir gün sonrasını hesapla.
- Eğer bilgi eksikse (ör. dosya ID'si) "explanation" alanında kullanıcıdan iste.
- Kesinlikle sadece JSON döndür, başka metin ekleme.
- Türkçe açıklamalar yaz.

DOCS KURALLARI:
- Kullanıcı belge / rapor / döküman oluşturmasını istiyorsa: create_document kullan.
- body_text'i mutlaka Markdown sözdizimi ile yaz (## başlıklar, * maddeler vb.).
- ASLA kısa ve yüzeysel içerik yazma. En az 4-6 bölüm, her bölümde dolu içerik olsun.
- "create_professional_document" birden fazla bölüm gerektiğinde tercih et.

SLIDES KURALLARI:
- Kullanıcı sunum oluşturmasını istiyorsa: KESİNLİKLE create_full_presentation kullan.
- Eski "create_presentation" veya "add_slide_with_text" tek başına yeterli değil.
- create_full_presentation ile en az 5-8 slayt üret.
- Her slaytın content alanı gerçek, bilgilendirici içerik içersin — \n ile maddelere böl.
- Sunum konusuna uygun bölüm ayırıcı (section: true) slaytlar ekle.
- theme parametresi: "blue" (iş/kurumsal), "teal" (teknoloji), "dark" (modern), "red" (güçlü/acil)."""


# -------------------- Niyet Analizi --------------------

def analyze_intent(user_message: str) -> dict | None:
    """
    Kullanıcının mesajını LLM ile analiz eder ve yapılandırılmış
    bir komut nesnesi döndürür.

    Args:
        user_message: Kullanıcının doğal dilde verdiği komut.

    Returns:
        dict: {"service": ..., "action": ..., "params": ..., "explanation": ...}
              veya hata durumunda None.
    """
    client, model_name, provider = _get_llm_client()

    if client is None:
        console.print("[red]✗ LLM istemcisi başlatılamadı.[/red]")
        return None

    try:
        console.print("[yellow]⟳ Niyet analiz ediliyor (Ollama — lokal)...[/yellow]")

        # Ollama'nın OpenAI-uyumlu API'si ile çağrı
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,  # Düşük sıcaklık → tutarlı JSON çıktılar
        )
        result_text = response.choices[0].message.content

        # JSON parse et
        result = _parse_json_response(result_text)

        if result:
            console.print(
                f"[green]✓ Niyet:[/green] {result.get('service', '?')} → "
                f"{result.get('action', '?')}"
            )
            return result
        else:
            console.print("[yellow]⚠ LLM yanıtı JSON olarak ayrıştırılamadı.[/yellow]")
            return None

    except Exception as e:
        console.print(f"[red]✗ LLM analiz hatası: {e}[/red]")
        return None


def _parse_json_response(text: str) -> dict | None:
    """
    LLM'den gelen yanıtı JSON olarak ayrıştırır.
    Markdown code block içinde olabilecek JSON'ı da destekler.

    Args:
        text: LLM'nin ham metin yanıtı.

    Returns:
        dict | None: Ayrıştırılmış JSON veya None.
    """
    # Önce doğrudan JSON parse dene
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Markdown code block: ```json ... ```
    if "```" in text:
        try:
            json_block = text.split("```json")[-1].split("```")[0].strip()
            return json.loads(json_block)
        except (json.JSONDecodeError, IndexError):
            pass

        try:
            json_block = text.split("```")[-2].strip()
            return json.loads(json_block)
        except (json.JSONDecodeError, IndexError):
            pass

    # İlk ve son süslü parantez arasını bul
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        pass

    return None


def get_chat_response(user_message: str) -> str:
    """
    Genel sohbet yanıtı üretir (Google servisleriyle ilgili olmayan sorular için).

    Args:
        user_message: Kullanıcının mesajı.

    Returns:
        str: LLM'nin sohbet yanıtı.
    """
    client, model_name, provider = _get_llm_client()

    if client is None:
        return "Ollama servisi kullanılamıyor. 'ollama serve' ile başlatın."

    try:
        chat_system = (
            "Sen yardımsever, nazik ve Türkçe konuşan bir kişisel asistansın. "
            "Kısa, öz ve faydalı yanıtlar ver."
        )

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": chat_system},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Yanıt üretilirken hata oluştu: {e}"


# -------------------- Doğrudan Test --------------------
if __name__ == "__main__":
    console.print(f"\n[bold cyan]{config.APP_NAME} — LLM Router Testi[/bold cyan]\n")

    test_commands = [
        "Drive'daki dosyalarımı listele",
        "Yarın saat 14'te toplantı ekle",
        "ali@example.com adresine 'Merhaba' konulu bir mail gönder",
        "Bugün hava nasıl?",
    ]

    for cmd in test_commands:
        console.print(f"\n[bold]Komut:[/bold] {cmd}")
        result = analyze_intent(cmd)
        if result:
            console.print(f"[dim]{json.dumps(result, ensure_ascii=False, indent=2)}[/dim]")
        console.print("─" * 50)
