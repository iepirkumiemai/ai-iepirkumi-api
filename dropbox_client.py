import os
import tempfile
from typing import List, Dict, Any

import dropbox
from dropbox.files import FileMetadata, FolderMetadata


class DropboxClient:
    """
    Pilns Dropbox klienta modulis priekš AI Iepirkumi API.
    Funkcionalitāte:
    • rekursīva mapju nolasīšana
    • failu tipu identifikācija
    • jebkura faila lejupielāde pagaidu mapē
    """

    def __init__(self, access_token: str):
        if not access_token:
            raise ValueError("Dropbox access token is missing")

        self.dbx = dropbox.Dropbox(access_token)

    # =====================================================================================
    # 1. Failu tipa atpazīšana
    # =====================================================================================
    @staticmethod
    def detect_file_type(filename: str) -> str:
        ext = filename.lower().split(".")[-1]
        if ext in ["pdf"]:
            return "pdf"
        if ext in ["docx"]:
            return "docx"
        if ext in ["doc"]:
            return "doc"
        if ext in ["zip"]:
            return "zip"
        if ext in ["edoc"]:
            return "edoc"
        return "unknown"

    # =====================================================================================
    # 2. Rekursīva mapju skenēšana
    # =====================================================================================
    def list_tree(self, path: str = "") -> List[Dict[str, Any]]:
        """
        Rekursīvi atgriež visus failus un mapes no norādītā Dropbox ceļa.
        Struktūra:
        [
            {
                "name": "faila_nosaukums.pdf",
                "path": "/projekts/fails.pdf",
                "type": "pdf"
            },
            ...
        ]
        """
        try:
            result = self.dbx.files_list_folder(path, recursive=True)
        except Exception as e:
            raise RuntimeError(f"Dropbox tree read error: {str(e)}")

        output = []

        for entry in result.entries:
            if isinstance(entry, FileMetadata):
                output.append({
                    "name": entry.name,
                    "path": entry.path_lower,
                    "type": self.detect_file_type(entry.name),
                    "size": entry.size
                })

        return output

    # =====================================================================================
    # 3. Failu lejupielāde pagaidu direktorijā
    # =====================================================================================
    def download_file(self, dropbox_path: str) -> str:
        """
        Lejupielādē failu no Dropbox un saglabā to pagaidu mapē.
        Atgriež lokālo faila ceļu.
        """
        try:
            _, ext = os.path.splitext(dropbox_path)
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
            os.close(tmp_fd)

            with open(tmp_path, "wb") as f:
                metadata, response = self.dbx.files_download(path=dropbox_path)
                f.write(response.content)

            return tmp_path

        except Exception as e:
            raise RuntimeError(f"Dropbox download error for {dropbox_path}: {str(e)}")
