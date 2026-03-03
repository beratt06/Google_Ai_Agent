# ===================================================
# docs_agent.py — Google Docs İşlemleri (Gelişmiş)
# ===================================================
# Profesyonel biçimlendirilmiş belge oluşturma,
# okuma, güncelleme ve içerik ekleme işlemleri.
# Markdown benzeri sözdizimini destekler:
#   # Başlık 1      → HEADING_1 (büyük, mavi, kalın)
#   ## Başlık 2     → HEADING_2 (orta, kalın)
#   ### Başlık 3    → HEADING_3 (küçük, kalın)
#   * madde / - m.  → Bullet list
#   --- veya ===    → Yatay çizgi (görsel ayırıcı)
#   Normal satır    → NORMAL_TEXT
# ===================================================

import re
from rich.console import Console

console = Console()

# ================================================================
# Renk Paletleri (RGB 0–1 arası)
# ================================================================
THEMES = {
    "blue": {
        "h1_color":   {"red": 0.07, "green": 0.24, "blue": 0.56},
        "h2_color":   {"red": 0.12, "green": 0.36, "blue": 0.64},
        "h3_color":   {"red": 0.18, "green": 0.47, "blue": 0.71},
        "body_color": {"red": 0.13, "green": 0.13, "blue": 0.13},
        "rule_color": {"red": 0.07, "green": 0.24, "blue": 0.56},
    },
    "dark": {
        "h1_color":   {"red": 0.10, "green": 0.10, "blue": 0.10},
        "h2_color":   {"red": 0.20, "green": 0.20, "blue": 0.20},
        "h3_color":   {"red": 0.30, "green": 0.30, "blue": 0.30},
        "body_color": {"red": 0.15, "green": 0.15, "blue": 0.15},
        "rule_color": {"red": 0.10, "green": 0.10, "blue": 0.10},
    },
}

DEFAULT_THEME = "blue"


# ================================================================
# Yardımcı: İçerik Ayrıştırıcı
# ================================================================

def _parse_body_text(text: str) -> list[dict]:
    """
    Markdown benzeri gövde metnini segment listesine çevirir.

    Her segment:
      {"text": "...", "type": "heading1|heading2|heading3|bullet|rule|body|empty"}
    """
    segments = []
    lines = text.split("\n")

    for line in lines:
        # Seviye 1 başlık: # Başlık
        if re.match(r"^# (.+)", line):
            content = re.sub(r"^# ", "", line).strip()
            segments.append({"text": content + "\n", "type": "heading1"})

        # Seviye 2 başlık: ## Başlık
        elif re.match(r"^## (.+)", line):
            content = re.sub(r"^## ", "", line).strip()
            segments.append({"text": content + "\n", "type": "heading2"})

        # Seviye 3 başlık: ### Başlık
        elif re.match(r"^### (.+)", line):
            content = re.sub(r"^### ", "", line).strip()
            segments.append({"text": content + "\n", "type": "heading3"})

        # Madde işareti: * / - / •
        elif re.match(r"^[\*\-•] (.+)", line):
            content = re.sub(r"^[\*\-•] ", "", line).strip()
            segments.append({"text": content + "\n", "type": "bullet"})

        # Numaralı liste: 1. / 2. vb.
        elif re.match(r"^\d+\. (.+)", line):
            content = re.sub(r"^\d+\. ", "", line).strip()
            segments.append({"text": content + "\n", "type": "numbered"})

        # Yatay çizgi: --- veya ===
        elif re.match(r"^[-=]{3,}$", line.strip()):
            segments.append({"text": "\n", "type": "rule"})

        # Boş satır
        elif line.strip() == "":
            segments.append({"text": "\n", "type": "empty"})

        # Normal metin
        else:
            segments.append({"text": line + "\n", "type": "body"})

    return segments


def _build_format_requests(segments: list[dict], base_index: int = 1, theme: str = DEFAULT_THEME) -> list[dict]:
    """
    Segment listesinden Google Docs batchUpdate request listesi üretir.
    """
    palette = THEMES.get(theme, THEMES[DEFAULT_THEME])
    requests = []
    idx = base_index

    for seg in segments:
        text = seg["text"]
        seg_len = len(text)
        seg_type = seg["type"]
        start = idx
        end = idx + seg_len
        text_range = {"startIndex": start, "endIndex": end}

        if seg_type == "heading1":
            requests.append({
                "updateParagraphStyle": {
                    "range": text_range,
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_1",
                        "spaceAbove": {"magnitude": 18, "unit": "PT"},
                        "spaceBelow": {"magnitude": 8, "unit": "PT"},
                    },
                    "fields": "namedStyleType,spaceAbove,spaceBelow",
                }
            })
            requests.append({
                "updateTextStyle": {
                    "range": text_range,
                    "textStyle": {
                        "bold": True,
                        "fontSize": {"magnitude": 22, "unit": "PT"},
                        "foregroundColor": {"color": {"rgbColor": palette["h1_color"]}},
                        "weightedFontFamily": {"fontFamily": "Google Sans"},
                    },
                    "fields": "bold,fontSize,foregroundColor,weightedFontFamily",
                }
            })

        elif seg_type == "heading2":
            requests.append({
                "updateParagraphStyle": {
                    "range": text_range,
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_2",
                        "spaceAbove": {"magnitude": 14, "unit": "PT"},
                        "spaceBelow": {"magnitude": 6, "unit": "PT"},
                    },
                    "fields": "namedStyleType,spaceAbove,spaceBelow",
                }
            })
            requests.append({
                "updateTextStyle": {
                    "range": text_range,
                    "textStyle": {
                        "bold": True,
                        "fontSize": {"magnitude": 16, "unit": "PT"},
                        "foregroundColor": {"color": {"rgbColor": palette["h2_color"]}},
                        "weightedFontFamily": {"fontFamily": "Google Sans"},
                    },
                    "fields": "bold,fontSize,foregroundColor,weightedFontFamily",
                }
            })

        elif seg_type == "heading3":
            requests.append({
                "updateParagraphStyle": {
                    "range": text_range,
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_3",
                        "spaceAbove": {"magnitude": 10, "unit": "PT"},
                        "spaceBelow": {"magnitude": 4, "unit": "PT"},
                    },
                    "fields": "namedStyleType,spaceAbove,spaceBelow",
                }
            })
            requests.append({
                "updateTextStyle": {
                    "range": text_range,
                    "textStyle": {
                        "bold": True,
                        "italic": False,
                        "fontSize": {"magnitude": 13, "unit": "PT"},
                        "foregroundColor": {"color": {"rgbColor": palette["h3_color"]}},
                        "weightedFontFamily": {"fontFamily": "Google Sans"},
                    },
                    "fields": "bold,italic,fontSize,foregroundColor,weightedFontFamily",
                }
            })

        elif seg_type in ("bullet", "numbered"):
            requests.append({
                "updateParagraphStyle": {
                    "range": text_range,
                    "paragraphStyle": {
                        "namedStyleType": "NORMAL_TEXT",
                        "spaceBelow": {"magnitude": 4, "unit": "PT"},
                        "indentStart": {"magnitude": 18, "unit": "PT"},
                    },
                    "fields": "namedStyleType,spaceBelow,indentStart",
                }
            })
            requests.append({
                "updateTextStyle": {
                    "range": text_range,
                    "textStyle": {
                        "fontSize": {"magnitude": 11, "unit": "PT"},
                        "foregroundColor": {"color": {"rgbColor": palette["body_color"]}},
                        "weightedFontFamily": {"fontFamily": "Arial"},
                    },
                    "fields": "fontSize,foregroundColor,weightedFontFamily",
                }
            })
            bullet_preset = "BULLET_DISC_CIRCLE_SQUARE" if seg_type == "bullet" else "NUMBERED_DECIMAL_ALPHA_ROMAN"
            requests.append({
                "createParagraphBullets": {
                    "range": text_range,
                    "bulletPreset": bullet_preset,
                }
            })

        elif seg_type == "body":
            requests.append({
                "updateParagraphStyle": {
                    "range": text_range,
                    "paragraphStyle": {
                        "namedStyleType": "NORMAL_TEXT",
                        "spaceBelow": {"magnitude": 8, "unit": "PT"},
                        "lineSpacing": 120,
                    },
                    "fields": "namedStyleType,spaceBelow,lineSpacing",
                }
            })
            requests.append({
                "updateTextStyle": {
                    "range": text_range,
                    "textStyle": {
                        "fontSize": {"magnitude": 11, "unit": "PT"},
                        "foregroundColor": {"color": {"rgbColor": palette["body_color"]}},
                        "weightedFontFamily": {"fontFamily": "Arial"},
                        "bold": False,
                        "italic": False,
                    },
                    "fields": "fontSize,foregroundColor,weightedFontFamily,bold,italic",
                }
            })

        idx = end

    return requests


# ================================================================
# Temel Fonksiyonlar
# ================================================================

def read_document(service, document_id: str) -> str:
    """
    Belirtilen Google Docs belgesinin tüm metin içeriğini okur.

    Args:
        service: Google Docs API servisi.
        document_id: Belge ID'si.

    Returns:
        str: Belgenin metin içeriği.
    """
    try:
        doc = service.documents().get(documentId=document_id).execute()
        title = doc.get("title", "Başlıksız Belge")
        content = doc.get("body", {}).get("content", [])

        # Belge içeriğindeki tüm metin öğelerini birleştir
        text_parts = []
        for element in content:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                for elem in paragraph.get("elements", []):
                    text_run = elem.get("textRun")
                    if text_run:
                        text_parts.append(text_run.get("content", ""))

        full_text = "".join(text_parts).strip()

        if not full_text:
            return f"'{title}' belgesi boş."

        result = f"📄 Belge: {title}\n{'─' * 40}\n{full_text}"
        console.print(f"[green]✓ '{title}' belgesi okundu ({len(full_text)} karakter).[/green]")
        return result

    except Exception as e:
        error_msg = f"Belge okunurken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def create_document(service, title: str, body_text: str = "", theme: str = DEFAULT_THEME) -> str:
    """
    Yeni bir Google Docs belgesi oluşturur ve isteğe bağlı olarak
    profesyonel biçimlendirilmiş içerik ekler.

    Markdown sözdizimi desteklenir:
      # Başlık 1  |  ## Başlık 2  |  ### Başlık 3
      * madde / - madde  (bullet list)
      1. madde (numaralı liste)
      ---  (ayırıcı)

    Args:
        service: Google Docs API servisi.
        title: Belge başlığı.
        body_text: Belgeye yazılacak metin (Markdown benzeri sözdizimi).
        theme: Renk teması ('blue' veya 'dark').

    Returns:
        str: Oluşturma sonucu mesajı (belge ID ve link dahil).
    """
    try:
        doc = service.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")
        doc_title = doc.get("title")
        console.print(f"[cyan]⟳ Belge '{doc_title}' oluşturuldu.[/cyan]")

        if body_text and body_text.strip():
            segments = _parse_body_text(body_text.strip())
            all_text = "".join(s["text"] for s in segments)

            # 1) Tüm metni tek seferde ekle
            service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": [
                    {"insertText": {"location": {"index": 1}, "text": all_text}}
                ]},
            ).execute()

            # 2) Biçimlendirme isteklerini uygula
            fmt_requests = _build_format_requests(segments, base_index=1, theme=theme)
            if fmt_requests:
                # Google Docs batchUpdate'in tek seferde alabileceği istek sayısı sınırlı;
                # 200'er parçalara bölerek gönder.
                for chunk_start in range(0, len(fmt_requests), 200):
                    chunk = fmt_requests[chunk_start: chunk_start + 200]
                    service.documents().batchUpdate(
                        documentId=doc_id, body={"requests": chunk}
                    ).execute()

            console.print(f"[green]✓ İçerik eklendi ve biçimlendirildi ({len(all_text)} karakter).[/green]")

        return (
            f"Belge başarıyla oluşturuldu!\n"
            f"  Başlık : {doc_title}\n"
            f"  ID     : {doc_id}\n"
            f"  Link   : https://docs.google.com/document/d/{doc_id}/edit"
        )

    except Exception as e:
        error_msg = f"Belge oluşturulurken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def create_professional_document(
    service,
    title: str,
    sections: list,
    theme: str = DEFAULT_THEME,
    add_toc_header: bool = True,
) -> str:
    """
    Bölüm listesinden tam biçimlendirilmiş profesyonel belge oluşturur.

    Args:
        service: Google Docs API servisi.
        title: Belge başlığı.
        sections: Bölüm listesi. Her eleman:
                  {"heading": "Bölüm Başlığı", "content": "Paragraf metni..."}
                  'heading' isteğe bağlıdır; sadece 'content' de geçerlidir.
        theme: 'blue' veya 'dark'.
        add_toc_header: True ise belgeye büyük bir kapak başlığı eklenir.

    Returns:
        str: Belge linki ve bilgiler.
    """
    try:
        doc = service.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")
        console.print(f"[cyan]⟳ Profesyonel belge '{title}' oluşturuluyor...[/cyan]")

        # Bölümleri düz Markdown metnine çevir
        lines = []
        if add_toc_header:
            lines.append(f"# {title}")
            lines.append("")

        for sec in sections:
            heading = sec.get("heading", "")
            content = sec.get("content", "")
            if heading:
                lines.append(f"## {heading}")
                lines.append("")
            if content:
                for para_line in content.strip().split("\n"):
                    lines.append(para_line)
                lines.append("")

        body_text = "\n".join(lines)
        segments = _parse_body_text(body_text.strip())
        all_text = "".join(s["text"] for s in segments)

        # 1) Metin ekle
        service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [
                {"insertText": {"location": {"index": 1}, "text": all_text}}
            ]},
        ).execute()

        # 2) Biçimlendirme
        fmt_requests = _build_format_requests(segments, base_index=1, theme=theme)
        for chunk_start in range(0, len(fmt_requests), 200):
            chunk = fmt_requests[chunk_start: chunk_start + 200]
            service.documents().batchUpdate(
                documentId=doc_id, body={"requests": chunk}
            ).execute()

        section_count = len(sections)
        console.print(
            f"[green]✓ Profesyonel belge oluşturuldu: {section_count} bölüm, "
            f"{len(all_text)} karakter.[/green]"
        )
        return (
            f"Profesyonel belge oluşturuldu!\n"
            f"  Başlık  : {title}\n"
            f"  Bölümler: {section_count}\n"
            f"  ID      : {doc_id}\n"
            f"  Link    : https://docs.google.com/document/d/{doc_id}/edit"
        )

    except Exception as e:
        error_msg = f"Profesyonel belge oluşturulurken hata: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def append_to_document(service, document_id: str, text: str, theme: str = DEFAULT_THEME) -> str:
    """
    Var olan bir Google Docs belgesinin sonuna biçimlendirilmiş metin ekler.
    Markdown benzeri sözdizimi desteklenir (# / ## / * vb.).

    Args:
        service: Google Docs API servisi.
        document_id: Belge ID'si.
        text: Eklenecek metin (Markdown destekli).
        theme: Renk teması.

    Returns:
        str: İşlem sonucu mesajı.
    """
    try:
        # Belgenin sonundaki yazılabilir index'i bul
        doc = service.documents().get(documentId=document_id).execute()
        body_content = doc.get("body", {}).get("content", [])

        end_index = 1
        for element in reversed(body_content):
            ei = element.get("endIndex")
            if ei is not None and ei > 1:
                end_index = ei - 1
                break

        # Metni segmentlere ayır
        segments = _parse_body_text(text.strip())
        all_text = "".join(s["text"] for s in segments)

        # 1) Metni ekle
        service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": [
                {"insertText": {"location": {"index": end_index}, "text": "\n" + all_text}}
            ]},
        ).execute()

        # 2) Biçimlendirme (metni 1 karakter ileriden başlatıyoruz — eklenen \n için)
        fmt_requests = _build_format_requests(segments, base_index=end_index + 1, theme=theme)
        if fmt_requests:
            for chunk_start in range(0, len(fmt_requests), 200):
                chunk = fmt_requests[chunk_start: chunk_start + 200]
                service.documents().batchUpdate(
                    documentId=document_id, body={"requests": chunk}
                ).execute()

        success_msg = f"Belgeye biçimlendirilmiş içerik eklendi ({len(all_text)} karakter)."
        console.print(f"[green]✓ {success_msg}[/green]")
        return success_msg

    except Exception as e:
        error_msg = f"Belgeye metin eklenirken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def update_document_title(service, document_id: str, new_title: str) -> str:
    """
    Bir Google Docs belgesinin başlığını günceller.

    Args:
        service: Google Docs API servisi.
        document_id: Belge ID'si.
        new_title: Yeni başlık.

    Returns:
        str: Güncelleme sonucu mesajı.
    """
    try:
        requests = [
            {
                "updateDocumentStyle": {
                    # Not: Başlık Drive API ile güncellenir, ancak
                    # Docs API'de title güncellemek için farklı yol kullanılır.
                    # Bu nedenle Drive API kullanıyoruz.
                }
            }
        ]

        # Drive API üzerinden başlık güncelleme (daha güvenilir)
        from googleapiclient.discovery import build
        from auth_google import authenticate

        creds = authenticate()
        drive_service = build("drive", "v3", credentials=creds)
        drive_service.files().update(
            fileId=document_id, body={"name": new_title}
        ).execute()

        success_msg = f"Belge başlığı '{new_title}' olarak güncellendi."
        console.print(f"[green]✓ {success_msg}[/green]")
        return success_msg

    except Exception as e:
        error_msg = f"Belge başlığı güncellenirken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg
