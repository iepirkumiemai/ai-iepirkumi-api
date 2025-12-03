import os
from typing import Optional

import dropbox


class DropboxClient:
    def __init__(self) -> None:
        token = os.getenv("DROPBOX_ACCESS_TOKEN")
        if not token:
            raise RuntimeError("DROPBOX_ACCESS_TOKEN environment variable is not set")
        self.dbx = dropbox.Dropbox(token)

    def download_file(self, path: str) -> bytes:
        """
        Lejupielādē failu no Dropbox pēc pilnā ceļa, piemēram:
        /AI-Iepirkumi/Nolikums_2025.pdf
        """
        metadata, file = self.dbx.files_download(path)
        return file.content

    def file_exists(self, path: str) -> bool:
        try:
            self.dbx.files_get_metadata(path)
            return True
        except dropbox.exceptions.ApiError:
            return False


_dropbox_client: Optional[DropboxClient] = None


def get_dropbox() -> DropboxClient:
    global _dropbox_client
    if _dropbox_client is None:
        _dropbox_client = DropboxClient()
    return _dropbox_client
