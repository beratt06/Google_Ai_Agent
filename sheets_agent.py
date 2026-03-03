# ===================================================
# sheets_agent.py — Google Sheets İşlemleri
# ===================================================
# Bu modül Google Sheets üzerinde tablo okuma, yazma,
# yeni spreadsheet oluşturma ve hücre güncelleme
# işlemlerini gerçekleştirir.
# ===================================================

from rich.console import Console
from rich.table import Table

console = Console()


def read_sheet(service, spreadsheet_id: str, range_name: str = "A1:Z100") -> str:
    """
    Google Sheets'ten belirtilen aralığı okur.

    Args:
        service: Google Sheets API servisi.
        spreadsheet_id: Spreadsheet ID'si.
        range_name: Okunacak hücre aralığı (ör: "Sayfa1!A1:D10").

    Returns:
        str: Okunan veri (tablo formatında).
    """
    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            return f"'{range_name}' aralığında veri bulunamadı."

        # Zengin tablo ile göster
        table = Table(title=f"Sheets: {range_name}", show_lines=True)

        # İlk satırı başlık olarak kullan
        headers = values[0] if values else []
        for h in headers:
            table.add_column(str(h), style="cyan")

        # Kalan satırları ekle
        for row in values[1:]:
            # Eksik sütunları boş string ile doldur
            padded_row = row + [""] * (len(headers) - len(row))
            table.add_row(*[str(cell) for cell in padded_row])

        console.print(table)

        # Düz metin çıktısı da döndür
        lines = []
        for row in values:
            lines.append(" | ".join(str(cell) for cell in row))
        return "\n".join(lines)

    except Exception as e:
        error_msg = f"Sheets verisi okunurken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def write_to_sheet(
    service, spreadsheet_id: str, range_name: str, values: list
) -> str:
    """
    Google Sheets'e veri yazar.

    Args:
        service: Google Sheets API servisi.
        spreadsheet_id: Spreadsheet ID'si.
        range_name: Yazılacak hücre aralığı (ör: "Sayfa1!A1").
        values: Yazılacak veriler — 2 boyutlu liste.
                Örnek: [["Ad", "Soyad"], ["Ali", "Yılmaz"]]

    Returns:
        str: Yazma sonucu mesajı.
    """
    try:
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",  # Formüller ve formatlar korunsun
                body=body,
            )
            .execute()
        )

        updated_cells = result.get("updatedCells", 0)
        updated_range = result.get("updatedRange", range_name)
        success_msg = f"{updated_cells} hücre güncellendi (Aralık: {updated_range})."
        console.print(f"[green]✓ {success_msg}[/green]")
        return success_msg

    except Exception as e:
        error_msg = f"Sheets'e yazılırken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def append_to_sheet(
    service, spreadsheet_id: str, range_name: str, values: list
) -> str:
    """
    Google Sheets'in sonuna yeni satır(lar) ekler.

    Args:
        service: Google Sheets API servisi.
        spreadsheet_id: Spreadsheet ID'si.
        range_name: Hedef tablo aralığı (ör: "Sayfa1!A:D").
        values: Eklenecek satırlar — 2 boyutlu liste.

    Returns:
        str: Ekleme sonucu mesajı.
    """
    try:
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )

        updates = result.get("updates", {})
        updated_rows = updates.get("updatedRows", 0)
        success_msg = f"{updated_rows} yeni satır eklendi."
        console.print(f"[green]✓ {success_msg}[/green]")
        return success_msg

    except Exception as e:
        error_msg = f"Sheets'e satır eklenirken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def create_spreadsheet(service, title: str, sheet_names: list = None) -> str:
    """
    Yeni bir Google Sheets dosyası oluşturur.

    Args:
        service: Google Sheets API servisi.
        title: Spreadsheet başlığı.
        sheet_names: Sayfa isimleri listesi (opsiyonel).
                     Örnek: ["Gelirler", "Giderler"]

    Returns:
        str: Oluşturma sonucu mesajı (spreadsheet ID dahil).
    """
    try:
        spreadsheet_body = {"properties": {"title": title}}

        # Özel sayfa isimleri belirtilmişse ekle
        if sheet_names:
            spreadsheet_body["sheets"] = [
                {"properties": {"title": name}} for name in sheet_names
            ]

        spreadsheet = (
            service.spreadsheets()
            .create(body=spreadsheet_body, fields="spreadsheetId,spreadsheetUrl")
            .execute()
        )

        ss_id = spreadsheet.get("spreadsheetId")
        ss_url = spreadsheet.get("spreadsheetUrl")

        success_msg = (
            f"Spreadsheet oluşturuldu!\n"
            f"  Başlık : {title}\n"
            f"  ID     : {ss_id}\n"
            f"  Link   : {ss_url}"
        )
        console.print(f"[green]✓ {success_msg}[/green]")
        return success_msg

    except Exception as e:
        error_msg = f"Spreadsheet oluşturulurken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg
