# ===================================================
# drive_agent.py — Google Drive İşlemleri
# ===================================================
# Bu modül Google Drive üzerinde dosya listeleme,
# arama ve indirme işlemlerini gerçekleştirir.
# ===================================================

import io
import os
from googleapiclient.http import MediaIoBaseDownload
from rich.console import Console
from rich.table import Table

console = Console()


def list_files(service, max_results: int = 10) -> str:
    """
    Google Drive'daki son dosyaları listeler.

    Args:
        service: Google Drive API servisi.
        max_results: Listelenecek maksimum dosya sayısı.

    Returns:
        str: Listeleme sonucu (kullanıcıya gösterilecek metin).
    """
    try:
        results = (
            service.files()
            .list(
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )
        files = results.get("files", [])

        if not files:
            return "Drive'da hiç dosya bulunamadı."

        # Zengin tablo ile göster
        table = Table(title="Google Drive Dosyaları", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Dosya Adı", style="cyan", min_width=30)
        table.add_column("Tür", style="magenta", width=20)
        table.add_column("Son Değişiklik", style="green", width=22)

        lines = []
        for i, f in enumerate(files, 1):
            mime = f.get("mimeType", "Bilinmiyor")
            # MIME türünü kısa ve okunabilir yap
            short_mime = mime.split(".")[-1] if "." in mime else mime.split("/")[-1]
            modified = f.get("modifiedTime", "?")[:19].replace("T", " ")
            table.add_row(str(i), f["name"], short_mime, modified)
            lines.append(f"{i}. {f['name']} (ID: {f['id']})")

        console.print(table)
        return "\n".join(lines)

    except Exception as e:
        error_msg = f"Drive dosyaları listelenirken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def search_files(service, query: str, max_results: int = 10) -> str:
    """
    Google Drive'da dosya arar.

    Args:
        service: Google Drive API servisi.
        query: Aranacak dosya adı veya anahtar kelime.
        max_results: Maksimum sonuç sayısı.

    Returns:
        str: Arama sonuçları.
    """
    try:
        # Drive API sorgu formatı: name contains 'anahtar kelime'
        search_query = f"name contains '{query}' and trashed = false"

        results = (
            service.files()
            .list(
                q=search_query,
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )
        files = results.get("files", [])

        if not files:
            return f"'{query}' ile eşleşen dosya bulunamadı."

        table = Table(title=f"Arama Sonuçları: '{query}'", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Dosya Adı", style="cyan", min_width=30)
        table.add_column("Tür", style="magenta", width=20)
        table.add_column("Dosya ID", style="yellow", width=40)

        lines = []
        for i, f in enumerate(files, 1):
            mime = f.get("mimeType", "Bilinmiyor")
            short_mime = mime.split(".")[-1] if "." in mime else mime.split("/")[-1]
            table.add_row(str(i), f["name"], short_mime, f["id"])
            lines.append(f"{i}. {f['name']} (ID: {f['id']})")

        console.print(table)
        return "\n".join(lines)

    except Exception as e:
        error_msg = f"Drive araması sırasında hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def download_file(service, file_id: str, save_path: str = None) -> str:
    """
    Google Drive'dan dosya indirir.

    Args:
        service: Google Drive API servisi.
        file_id: İndirilecek dosyanın Google Drive ID'si.
        save_path: Dosyanın kaydedileceği yerel yol (None ise otomatik belirlenir).

    Returns:
        str: İndirme sonucu mesajı.
    """
    try:
        # Dosya bilgilerini al
        file_metadata = (
            service.files().get(fileId=file_id, fields="name, mimeType").execute()
        )
        file_name = file_metadata.get("name", "indirilen_dosya")
        mime_type = file_metadata.get("mimeType", "")

        # Google Workspace dosyalarını dışa aktar
        export_mime_map = {
            "application/vnd.google-apps.document": (
                "application/pdf",
                f"{file_name}.pdf",
            ),
            "application/vnd.google-apps.spreadsheet": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                f"{file_name}.xlsx",
            ),
            "application/vnd.google-apps.presentation": (
                "application/pdf",
                f"{file_name}.pdf",
            ),
        }

        # İndirme dizinini oluştur
        download_dir = "downloads"
        os.makedirs(download_dir, exist_ok=True)

        if mime_type in export_mime_map:
            export_mime, export_name = export_mime_map[mime_type]
            request = service.files().export_media(
                fileId=file_id, mimeType=export_mime
            )
            final_name = save_path or os.path.join(download_dir, export_name)
        else:
            request = service.files().get_media(fileId=file_id)
            final_name = save_path or os.path.join(download_dir, file_name)

        # Dosyayı indir (ilerleme çubuğu ile)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False

        console.print(f"[cyan]⟳ İndiriliyor: {file_name}...[/cyan]")
        while not done:
            status, done = downloader.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                console.print(f"  İlerleme: %{progress}", end="\r")

        # Dosyaya yaz
        with open(final_name, "wb") as f:
            f.write(fh.getvalue())

        success_msg = f"Dosya başarıyla indirildi: {final_name}"
        console.print(f"[green]✓ {success_msg}[/green]")
        return success_msg

    except Exception as e:
        error_msg = f"Dosya indirilirken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg


def get_file_info(service, file_id: str) -> str:
    """
    Belirtilen dosyanın detaylı bilgilerini döndürür.

    Args:
        service: Google Drive API servisi.
        file_id: Dosya ID'si.

    Returns:
        str: Dosya bilgileri.
    """
    try:
        file_meta = (
            service.files()
            .get(
                fileId=file_id,
                fields="id, name, mimeType, size, modifiedTime, createdTime, owners, shared",
            )
            .execute()
        )

        info_lines = [
            f"📄 Dosya Adı   : {file_meta.get('name', '?')}",
            f"🆔 Dosya ID    : {file_meta.get('id', '?')}",
            f"📁 MIME Türü   : {file_meta.get('mimeType', '?')}",
            f"📏 Boyut       : {file_meta.get('size', 'N/A')} bytes",
            f"📅 Oluşturulma : {file_meta.get('createdTime', '?')[:19]}",
            f"🔄 Değişiklik  : {file_meta.get('modifiedTime', '?')[:19]}",
            f"👤 Sahip       : {file_meta.get('owners', [{}])[0].get('displayName', '?')}",
            f"🔗 Paylaşıldı  : {'Evet' if file_meta.get('shared') else 'Hayır'}",
        ]

        result = "\n".join(info_lines)
        console.print(result)
        return result

    except Exception as e:
        error_msg = f"Dosya bilgisi alınırken hata oluştu: {e}"
        console.print(f"[red]✗ {error_msg}[/red]")
        return error_msg
