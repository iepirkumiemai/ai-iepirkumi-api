import tempfile
import zipfile
from pathlib import Path
from typing import List, Dict, Any

from PyPDF2 import PdfReader
import docx

from edoc_extractor import is_edoc, unpack_edoc, EdocError


class DocumentParserError(Exception):
    pass


class DocumentParser:
    """
    Universālais dokumentu parseris AI Tender sistēmai.
    Spēj apstrādāt: PDF, DOCX, DOC, TXT, RTF, ZIP, EDOC.
    Atgriež strukturētu rezultātu:
    {
        "filename": "...",
        "text": "... pilns teksts ...",
        "chunks": [...],
        "type": "pdf/docx/zip/edoc",
    }
    """

    # =========================================================
    # PDF
    # =========================================================
    @staticmethod
    def extract_pdf(path: Path) -> str:
        try:
            reader = PdfReader(str(path))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
            return text
        except Exception as e:
            raise DocumentParserError(f"PDF extraction error: {e}")

    # =========================================================
    # DOCX
    # =========================================================
    @staticmethod
    def extract_docx(path: Path) -> str:
        try:
            d = docx.Document(str(path))
            return "\n".join(p.text for p in d.paragraphs)
        except Exception as e:
            raise DocumentParserError(f"DOCX extraction error: {e}")

    # =========================================================
    # ZIP
    # =========================================================
    @staticmethod
    def extract_zip(path: Path) -> str:
        tmp_dir = Path(tempfile.mkdtemp(prefix="zip_"))
        texts = []

        try:
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(tmp_dir)
        except Exception as e:
            raise DocumentParserError(f"ZIP extraction error: {e}")

        for file in tmp_dir.rglob("*"):
            if not file.is_file():
                continue

            ext = file.suffix.lower()

            if ext == ".pdf":
                texts.append(DocumentParser.extract_pdf(file))
            elif ext == ".docx":
                texts.append(DocumentParser.extract_docx(file))
            elif ext in {".txt", ".rtf"}:
                texts.append(file.read_text(encoding="utf-8", errors="ignore"))
            else:
                texts.append(f"[UNSUPPORTED ZIP ITEM: {file.name}]")

        return "\n\n-----\n\n".join(texts)

    # =========================================================
    # EDOC
    # =========================================================
    @staticmethod
    def extract_edoc(path: Path) -> str:
        try:
            inner_files = unpack_edoc(path)
        except EdocError as e:
            raise DocumentParserError(f"EDOC extraction error: {e}")

        texts = []

        for f in inner_files:
            ext = f.suffix.lower()

            if ext == ".pdf":
                texts.append(DocumentParser.extract_pdf(f))
            elif ext == ".docx":
                texts.append(DocumentParser.extract_docx(f))
            elif ext in {".txt", ".rtf"}:
                texts.append(f.read_text(encoding="utf-8", errors="ignore"))
            else:
                texts.append(f"[UNSUPPORTED EDOC ITEM: {f.name}]")

        return "\n\n-----\n\n".join(texts)

    # =========================================================
    # UNIVERSĀLĀ FUNKCIJA
    # =========================================================
    @staticmethod
    def extract(path: Path) -> Dict[str, Any]:
        """
        Atgriež strukturētu rezultātu.
        """
        path = Path(path)
        ext = path.suffix.lower()

        # EDOC
        if is_edoc(path):
            text = DocumentParser.extract_edoc(path)
            return {
                "filename": path.name,
                "text": text,
                "chunks": text.split("\n\n"),
                "type": "edoc"
            }

        # PDF
        if ext == ".pdf":
            text = DocumentParser.extract_pdf(path)
            return {
                "filename": path.name,
                "text": text,
                "chunks": text.split("\n\n"),
                "type": "pdf"
            }

        # DOCX
        if ext == ".docx":
            text = DocumentParser.extract_docx(path)
            return {
                "filename": path.name,
                "text": text,
                "chunks": text.split("\n\n"),
                "type": "docx"
            }

        # TXT / RTF
        if ext in {".txt", ".rtf"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            return {
                "filename": path.name,
                "text": text,
                "chunks": text.split("\n\n"),
                "type": "text"
            }

        # ZIP
        if ext == ".zip":
            text = DocumentParser.extract_zip(path)
            return {
                "filename": path.name,
                "text": text,
                "chunks": text.split("\n\n"),
                "type": "zip"
            }

        raise DocumentParserError(f"Unsupported file type: {ext}")
