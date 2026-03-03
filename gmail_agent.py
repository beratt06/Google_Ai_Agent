# ===================================================
# gmail_agent.py — Gmail İşlemleri
# ===================================================
# Bu modül Gmail üzerinde taslak oluşturma, doğrudan
# mail gönderme ve gelen kutusu listeleme işlemlerini
# gerçekleştirir.
# ===================================================

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from rich.console import Console
from rich.table import Table

console = Console()


def _create_message(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> dict:
    """
    RFC 2822 uyumlu bir e-posta mesaj nesnesi oluşturur (yardımcı fonksiyon).

    Args:
        to: Alıcı e-posta adresi.
        subject: Konu satırı.
        body: E-posta gövdesi (düz metin).
        cc: Karbon kopya adresleri (virgülle ayrılmış).
        bcc: Gizli karbon kopya adresleri (virgülle ayrılmış).

    Returns:
        dict: Gmail API formatında {"raw": base64_encoded_message} nesnesi.
    """
    message = MIMEMultipart()
    message["to"] = to
    message["subject"] = subject

    if cc:
        message["cc"] = cc
    if bcc:
        message["bcc"] = bcc

    # Metin içeriği ekle (UTF-8 kodlama)
    msg_body = MIMEText(body, "plain", "utf-8")
    message.attach(msg_body)

    # Base64 URL-safe encode
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"raw": raw}


def send_email(
    service,
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
) -> str:
    """
    Gmail üzerinden doğrudan e-posta gönderir.

    Args:
        service: Gmail API servisi.
        to: Alıcı adresi.
        subject: Mail konusu.
        body: Mail gövdesi.
        cc: Karbon kopya (opsiyonel).
        bcc: Gizli kopya (opsiyonel).

    Returns:
        str: Gönderim sonucu mesajı.
    """
    try:
        message = _create_message(to, subject, body, cc, bcc)
        sent_message = (
            service.users()
            .messages()
            .send(userId="me", body=message)
            .execute()
        )

        msg_id = sent_message.get("id", "?")
        success_msg = (
            f"E-posta gönderildi!\n"
            f"  📧 Alıcı : {to}\n"
            f"  📋 Konu  : {subject}\n"
            f"  🆔 ID    : {msg_id}"
        )
        console.print(f"[green]✓ E-posta gönderildi: '{subject}' → {to}[/green]")
        return success_msg

    except Exception as e:
        error_msg = f"E-posta gönderilirken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def create_draft(
    service,
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
) -> str:
    """
    Gmail'de taslak (draft) oluşturur.

    Args:
        service: Gmail API servisi.
        to: Alıcı adresi.
        subject: Mail konusu.
        body: Mail gövdesi.
        cc: Karbon kopya (opsiyonel).
        bcc: Gizli kopya (opsiyonel).

    Returns:
        str: Taslak oluşturma sonucu mesajı.
    """
    try:
        message = _create_message(to, subject, body, cc, bcc)
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body={"message": message})
            .execute()
        )

        draft_id = draft.get("id", "?")
        success_msg = (
            f"Taslak oluşturuldu!\n"
            f"  📧 Alıcı : {to}\n"
            f"  📋 Konu  : {subject}\n"
            f"  🆔 ID    : {draft_id}"
        )
        console.print(f"[green]✓ Taslak oluşturuldu: '{subject}'[/green]")
        return success_msg

    except Exception as e:
        error_msg = f"Taslak oluşturulurken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def list_messages(service, max_results: int = 10, query: str = "") -> str:
    """
    Gmail gelen kutusundaki son mesajları listeler.

    Args:
        service: Gmail API servisi.
        max_results: Gösterilecek maksimum mesaj sayısı.
        query: Gmail arama sorgusu (ör: "from:ali@example.com",
               "is:unread", "subject:toplantı").

    Returns:
        str: Mesaj listesi.
    """
    try:
        results = (
            service.users()
            .messages()
            .list(userId="me", maxResults=max_results, q=query)
            .execute()
        )
        messages = results.get("messages", [])

        if not messages:
            return "Gelen kutusunda mesaj bulunamadı."

        # Mesaj detaylarını al
        table = Table(title="📬 Gmail Gelen Kutusu", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Gönderen", style="cyan", min_width=25)
        table.add_column("Konu", style="green", min_width=30)
        table.add_column("Tarih", style="yellow", width=18)

        lines = []
        for i, msg in enumerate(messages, 1):
            msg_detail = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="metadata",
                     metadataHeaders=["From", "Subject", "Date"])
                .execute()
            )

            headers = msg_detail.get("payload", {}).get("headers", [])
            header_dict = {h["name"]: h["value"] for h in headers}

            sender = header_dict.get("From", "Bilinmiyor")
            subject = header_dict.get("Subject", "(Konu yok)")
            date = header_dict.get("Date", "?")

            # Gönderen adını kısalt
            if "<" in sender:
                sender_display = sender.split("<")[0].strip().strip('"')
            else:
                sender_display = sender

            table.add_row(str(i), sender_display[:30], subject[:40], date[:18])
            lines.append(f"{i}. [{sender_display}] {subject}")

        console.print(table)
        return "\n".join(lines)

    except Exception as e:
        error_msg = f"Mesajlar listelenirken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def read_message(service, message_id: str) -> str:
    """
    Belirtilen Gmail mesajının tam içeriğini okur.

    Args:
        service: Gmail API servisi.
        message_id: Mesaj ID'si.

    Returns:
        str: Mesaj içeriği.
    """
    try:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        headers = msg.get("payload", {}).get("headers", [])
        header_dict = {h["name"]: h["value"] for h in headers}

        sender = header_dict.get("From", "Bilinmiyor")
        subject = header_dict.get("Subject", "(Konu yok)")
        date = header_dict.get("Date", "?")

        # Mesaj gövdesini çıkar
        body_text = ""
        payload = msg.get("payload", {})

        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode("utf-8")
                        break
        else:
            data = payload.get("body", {}).get("data", "")
            if data:
                body_text = base64.urlsafe_b64decode(data).decode("utf-8")

        result = (
            f"📧 Gönderen: {sender}\n"
            f"📋 Konu   : {subject}\n"
            f"📅 Tarih  : {date}\n"
            f"{'─' * 40}\n"
            f"{body_text.strip() if body_text else '(Metin içeriği bulunamadı)'}"
        )
        console.print(f"[green]✓ Mesaj okundu: '{subject}'[/green]")
        return result

    except Exception as e:
        error_msg = f"Mesaj okunurken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg
