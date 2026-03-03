# ===================================================
# slides_agent.py — Google Slides İşlemleri (Gelişmiş)
# ===================================================
# Tam profesyonel sunum oluşturma:
#   • Kapak slaytı (renkli arka plan, büyük başlık)
#   • İçerik slaytları (başlık + madde işaretli içerik)
#   • Birden fazla renk teması (blue / teal / dark / red)
#   • Toplu batchUpdate (minimum API çağrısı)
#   • add_slide_with_text: var olan sunuma slayt ekleme
# ===================================================

import uuid
from rich.console import Console

console = Console()

# ================================================================
# Renk Temaları  (RGB 0.0–1.0)
# ================================================================
SLIDE_THEMES = {
    "blue": {
        "title_bg":    {"red": 0.07, "green": 0.20, "blue": 0.46},
        "title_fg":    {"red": 1.00, "green": 1.00, "blue": 1.00},
        "subtitle_fg": {"red": 0.78, "green": 0.87, "blue": 1.00},
        "content_bg":  {"red": 1.00, "green": 1.00, "blue": 1.00},
        "accent":      {"red": 0.07, "green": 0.20, "blue": 0.46},
        "body_fg":     {"red": 0.15, "green": 0.15, "blue": 0.15},
        "divider_bg":  {"red": 0.10, "green": 0.29, "blue": 0.62},
        "divider_fg":  {"red": 1.00, "green": 1.00, "blue": 1.00},
    },
    "teal": {
        "title_bg":    {"red": 0.00, "green": 0.33, "blue": 0.34},
        "title_fg":    {"red": 1.00, "green": 1.00, "blue": 1.00},
        "subtitle_fg": {"red": 0.76, "green": 0.96, "blue": 0.93},
        "content_bg":  {"red": 1.00, "green": 1.00, "blue": 1.00},
        "accent":      {"red": 0.00, "green": 0.44, "blue": 0.45},
        "body_fg":     {"red": 0.12, "green": 0.12, "blue": 0.12},
        "divider_bg":  {"red": 0.00, "green": 0.38, "blue": 0.40},
        "divider_fg":  {"red": 1.00, "green": 1.00, "blue": 1.00},
    },
    "dark": {
        "title_bg":    {"red": 0.09, "green": 0.09, "blue": 0.12},
        "title_fg":    {"red": 1.00, "green": 1.00, "blue": 1.00},
        "subtitle_fg": {"red": 0.72, "green": 0.73, "blue": 0.80},
        "content_bg":  {"red": 0.13, "green": 0.13, "blue": 0.17},
        "accent":      {"red": 0.26, "green": 0.56, "blue": 1.00},
        "body_fg":     {"red": 0.88, "green": 0.88, "blue": 0.92},
        "divider_bg":  {"red": 0.18, "green": 0.18, "blue": 0.24},
        "divider_fg":  {"red": 1.00, "green": 1.00, "blue": 1.00},
    },
    "red": {
        "title_bg":    {"red": 0.60, "green": 0.07, "blue": 0.10},
        "title_fg":    {"red": 1.00, "green": 1.00, "blue": 1.00},
        "subtitle_fg": {"red": 1.00, "green": 0.82, "blue": 0.83},
        "content_bg":  {"red": 1.00, "green": 1.00, "blue": 1.00},
        "accent":      {"red": 0.65, "green": 0.09, "blue": 0.12},
        "body_fg":     {"red": 0.15, "green": 0.10, "blue": 0.10},
        "divider_bg":  {"red": 0.72, "green": 0.10, "blue": 0.13},
        "divider_fg":  {"red": 1.00, "green": 1.00, "blue": 1.00},
    },
}

DEFAULT_THEME = "blue"


# ================================================================
# Yardımcı İstek Üreticileri
# ================================================================

def _bg_request(object_id: str, rgb: dict) -> dict:
    return {
        "updatePageProperties": {
            "objectId": object_id,
            "pageProperties": {
                "pageBackgroundFill": {
                    "solidFill": {"color": {"rgbColor": rgb}}
                }
            },
            "fields": "pageBackgroundFill",
        }
    }


def _insert_text(object_id: str, text: str, index: int = 0) -> dict:
    return {
        "insertText": {
            "objectId": object_id,
            "insertionIndex": index,
            "text": text,
        }
    }


def _text_style(
    object_id: str,
    rgb: dict,
    font_size: int,
    bold: bool = False,
    font_family: str = "Google Sans",
) -> dict:
    return {
        "updateTextStyle": {
            "objectId": object_id,
            "style": {
                "bold": bold,
                "fontSize": {"magnitude": font_size, "unit": "PT"},
                "foregroundColor": {"opaqueColor": {"rgbColor": rgb}},
                "fontFamily": font_family,
            },
            "fields": "bold,fontSize,foregroundColor,fontFamily",
        }
    }


def _para_alignment(object_id: str, alignment: str = "CENTER") -> dict:
    return {
        "updateParagraphStyle": {
            "objectId": object_id,
            "style": {"alignment": alignment},
            "fields": "alignment",
        }
    }


# ================================================================
# Temel Fonksiyonlar
# ================================================================

def read_presentation(service, presentation_id: str) -> str:
    """Belirtilen Google Slides sunumunun içeriğini okur."""
    try:
        presentation = (
            service.presentations().get(presentationId=presentation_id).execute()
        )
        title = presentation.get("title", "Başlıksız Sunum")
        slides = presentation.get("slides", [])

        if not slides:
            return f"'{title}' sunumu boş — hiç slayt yok."

        output_lines = [
            f"🎞️  Sunum : {title}",
            f"📊 Toplam: {len(slides)} slayt",
            "─" * 50,
        ]

        for i, slide in enumerate(slides, 1):
            output_lines.append(f"\n▸ Slayt {i}")
            for element in slide.get("pageElements", []):
                shape = element.get("shape", {})
                for te in shape.get("text", {}).get("textElements", []):
                    tr = te.get("textRun")
                    if tr:
                        content = tr.get("content", "").strip()
                        if content:
                            output_lines.append(f"  {content}")

        result = "\n".join(output_lines)
        console.print(
            f"[green]✓ '{title}' sunumu okundu ({len(slides)} slayt).[/green]"
        )
        return result

    except Exception as e:
        error_msg = f"Sunum okunurken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def create_presentation(service, title: str) -> str:
    """Yeni boş bir Google Slides sunumu oluşturur."""
    try:
        presentation = service.presentations().create(body={"title": title}).execute()
        pres_id = presentation.get("presentationId")
        return (
            f"Sunum oluşturuldu!\n"
            f"  Başlık : {title}\n"
            f"  ID     : {pres_id}\n"
            f"  Link   : https://docs.google.com/presentation/d/{pres_id}/edit"
        )
    except Exception as e:
        error_msg = f"Sunum oluşturulurken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def add_slide_with_text(
    service,
    presentation_id: str,
    title_text: str,
    body_text: str = "",
    theme: str = DEFAULT_THEME,
) -> str:
    """
    Var olan bir sunuma biçimlendirilmiş yeni bir slayt ekler.

    Args:
        service: Google Slides API servisi.
        presentation_id: Sunum ID'si.
        title_text: Slayt başlığı.
        body_text: Slayt içeriği (maddeler yeni satırla ayrılır).
        theme: Renk teması.
    """
    try:
        palette = SLIDE_THEMES.get(theme, SLIDE_THEMES[DEFAULT_THEME])
        slide_id   = f"slide_{uuid.uuid4().hex[:8]}"
        title_id   = f"t_{uuid.uuid4().hex[:8]}"
        body_id    = f"b_{uuid.uuid4().hex[:8]}"

        placeholder_mappings = [
            {
                "layoutPlaceholder": {"type": "TITLE", "index": 0},
                "objectId": title_id,
            }
        ]
        if body_text:
            placeholder_mappings.append(
                {
                    "layoutPlaceholder": {"type": "BODY", "index": 0},
                    "objectId": body_id,
                }
            )

        requests = [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
                    "placeholderIdMappings": placeholder_mappings,
                }
            },
            _bg_request(slide_id, palette["content_bg"]),
            _insert_text(title_id, title_text),
            _text_style(title_id, palette["accent"], 28, bold=True),
        ]

        if body_text:
            requests += [
                _insert_text(body_id, body_text),
                _text_style(body_id, palette["body_fg"], 18, font_family="Arial"),
            ]

        service.presentations().batchUpdate(
            presentationId=presentation_id, body={"requests": requests}
        ).execute()

        console.print(f"[green]✓ Slayt eklendi: '{title_text}'[/green]")
        return f"Slayt eklendi: '{title_text}'"

    except Exception as e:
        error_msg = f"Slayt eklenirken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


# ================================================================
# Ana Fonksiyon: Tam Profesyonel Sunum Oluşturma
# ================================================================

def create_full_presentation(
    service,
    title: str,
    slides: list,
    subtitle: str = "",
    theme: str = DEFAULT_THEME,
) -> str:
    """
    Kapak slaytı dahil tam profesyonel bir sunum oluşturur.

    Args:
        service   : Google Slides API servisi.
        title     : Sunum başlığı (kapak slaytında görünür).
        slides    : Slayt listesi. Her eleman bir dict:
                    {
                      "title":   "Slayt başlığı",
                      "content": "Madde 1\\nMadde 2\\nMadde 3",
                      "layout":  "TITLE_AND_BODY" | "TITLE_ONLY" | "SECTION_HEADER",
                      "section": True   → bölüm ayırıcı slayt yapar
                    }
        subtitle  : Kapak slaytının alt yazısı (boş bırakılırsa otomatik oluşturulur).
        theme     : Renk teması: 'blue' | 'teal' | 'dark' | 'red'.

    Returns:
        str: Oluşturma sonucu (link dahil).
    """
    try:
        palette = SLIDE_THEMES.get(theme, SLIDE_THEMES[DEFAULT_THEME])

        # ── 1. Sunumu oluştur ──────────────────────────────────────
        pres = service.presentations().create(body={"title": title}).execute()
        pres_id = pres.get("presentationId")
        console.print(f"[cyan]⟳ Sunum '{title}' başlatıldı...[/cyan]")

        first_slide    = pres.get("slides", [{}])[0]
        first_slide_id = first_slide.get("objectId", "")

        # ── 2. Kapak slaytı ────────────────────────────────────────
        all_requests = [_bg_request(first_slide_id, palette["title_bg"])]

        cover_title_id    = None
        cover_subtitle_id = None
        for el in first_slide.get("pageElements", []):
            ph = el.get("shape", {}).get("placeholder", {})
            ph_type = ph.get("type", "")
            if ph_type in ("TITLE", "CENTERED_TITLE"):
                cover_title_id = el.get("objectId")
            elif ph_type in ("SUBTITLE", "BODY"):
                cover_subtitle_id = el.get("objectId")

        if cover_title_id:
            all_requests += [
                _insert_text(cover_title_id, title),
                _text_style(cover_title_id, palette["title_fg"], 40, bold=True),
                _para_alignment(cover_title_id, "CENTER"),
            ]

        if cover_subtitle_id:
            sub = subtitle or f"{len(slides)} Slayt  •  {theme.capitalize()} Tema"
            all_requests += [
                _insert_text(cover_subtitle_id, sub),
                _text_style(cover_subtitle_id, palette["subtitle_fg"], 22),
                _para_alignment(cover_subtitle_id, "CENTER"),
            ]

        # ── 3. İçerik ve bölüm slaytları ──────────────────────────
        for slide_data in slides:
            slide_id   = f"slide_{uuid.uuid4().hex[:8]}"
            s_title_id = f"t_{uuid.uuid4().hex[:8]}"
            s_body_id  = f"b_{uuid.uuid4().hex[:8]}"

            s_title    = slide_data.get("title", "")
            s_content  = slide_data.get("content", "")
            is_section = slide_data.get("section", False)

            # Bölüm ayırıcı slayt
            if is_section:
                all_requests.append({
                    "createSlide": {
                        "objectId": slide_id,
                        "slideLayoutReference": {"predefinedLayout": "SECTION_HEADER"},
                        "placeholderIdMappings": [
                            {
                                "layoutPlaceholder": {"type": "TITLE", "index": 0},
                                "objectId": s_title_id,
                            }
                        ],
                    }
                })
                all_requests += [
                    _bg_request(slide_id, palette["divider_bg"]),
                    _insert_text(s_title_id, s_title),
                    _text_style(s_title_id, palette["divider_fg"], 36, bold=True),
                    _para_alignment(s_title_id, "CENTER"),
                ]
                continue

            # Normal içerik slaytı
            layout = slide_data.get("layout", "TITLE_AND_BODY")
            placeholder_mappings = [
                {
                    "layoutPlaceholder": {"type": "TITLE", "index": 0},
                    "objectId": s_title_id,
                }
            ]
            if s_content and layout == "TITLE_AND_BODY":
                placeholder_mappings.append(
                    {
                        "layoutPlaceholder": {"type": "BODY", "index": 0},
                        "objectId": s_body_id,
                    }
                )

            all_requests.append({
                "createSlide": {
                    "objectId": slide_id,
                    "slideLayoutReference": {"predefinedLayout": layout},
                    "placeholderIdMappings": placeholder_mappings,
                }
            })
            all_requests.append(_bg_request(slide_id, palette["content_bg"]))

            if s_title:
                all_requests += [
                    _insert_text(s_title_id, s_title),
                    _text_style(s_title_id, palette["accent"], 28, bold=True),
                ]

            if s_content and layout == "TITLE_AND_BODY":
                all_requests += [
                    _insert_text(s_body_id, s_content),
                    _text_style(s_body_id, palette["body_fg"], 18, font_family="Arial"),
                ]

        # ── 4. Toplu batchUpdate (50'lik parçalar) ─────────────────
        CHUNK = 50
        error_count = 0
        for i in range(0, len(all_requests), CHUNK):
            chunk = all_requests[i: i + CHUNK]
            try:
                service.presentations().batchUpdate(
                    presentationId=pres_id, body={"requests": chunk}
                ).execute()
            except Exception as chunk_err:
                error_count += 1
                console.print(
                    f"[yellow]⚠ Grup {i // CHUNK + 1} hatası: {chunk_err}[/yellow]"
                )

        total = 1 + len(slides)
        status = "başarıyla" if error_count == 0 else f"{error_count} hatayla"
        console.print(
            f"[green]✓ Sunum {status} oluşturuldu: {total} slayt, tema: {theme}[/green]"
        )
        return (
            f"Profesyonel sunum oluşturuldu!\n"
            f"  Başlık  : {title}\n"
            f"  Slaytlar: {total} ({len(slides)} içerik + 1 kapak)\n"
            f"  Tema    : {theme}\n"
            f"  ID      : {pres_id}\n"
            f"  Link    : https://docs.google.com/presentation/d/{pres_id}/edit"
        )

    except Exception as e:
        error_msg = f"Sunum oluşturulurken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg
