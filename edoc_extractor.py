# edoc_extractor.py

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Iterable

# Pēc noklusējuma – ko mēs ņemam no EDOC iekšienes analīzei
SUPPORTED_INNER_EXTS = {
    ".pdf",
    ".docx",
    ".doc",
    ".txt",
    ".rtf",
    ".odt",
}


class EdocError(Exception):
    """Vispārēja kļūda, apstrādājot EDOC konteineru."""


def is_edoc(path: Path) -> bool:
    """
    Vienkārša pārbaude, vai fails izskatās pēc .edoc (pēc paplašinājuma).
    """
    return path.suffix.lower() == ".edoc"


def unpack_edoc(edoc_file: Path, work_dir: Path | None = None) -> List[Path]:
    """
    Atver .edoc (ASiC-E/ZIP) konteineru, izvelk tikai
    atbalstītos dokumentus un atgriež to ceļus.

    :param edoc_file: Ceļš uz .edoc failu.
    :param work_dir:  Pagaidu darba direktorija (ja None – izveido pats).
    :return:          Saraksts ar izvilkto failu ceļiem.
    """
    edoc_file = Path(edoc_file)

    if not edoc_file.is_file():
        raise EdocError(f"EDOC fails '{edoc_file}' neeksistē vai nav fails.")

    if work_dir is None:
        # Izveido pagaidu direktoriju vienam EDOC apstrādes ciklam
        tmp_root = Path(tempfile.mkdtemp(prefix="edoc_"))
    else:
        tmp_root = Path(work_dir)
        tmp_root.mkdir(parents=True, exist_ok=True)

    extracted_files: List[Path] = []

    try:
        with zipfile.ZipFile(edoc_file, mode="r") as zf:
            for member in zf.infolist():
                # Ignorē mapes
                if member.is_dir():
                    continue

                inner_name = member.filename
                inner_suffix = Path(inner_name).suffix.lower()

                # Ignorē tipiskos paraksta/metadatu failus
                if inner_suffix in {".p7s", ".p7m", ".xml"} and "signature" in inner_name.lower():
                    continue

                # Mūs interesē tikai konkrēti dokumentu tipi
                if inner_suffix not in SUPPORTED_INNER_EXTS:
                    continue

                # Saglabājam failu “plakanā” struktūrā (bez dziļām mapēm)
                target_path = tmp_root / Path(inner_name).name

                with zf.open(member, "r") as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                extracted_files.append(target_path)

    except zipfile.BadZipFile as exc:
        raise EdocError(
            f"Fails '{edoc_file}' nav derīgs EDOC/ZIP konteineris."
        ) from exc

    return extracted_files


def debug_list_edoc(edoc_file: Path) -> Iterable[str]:
    """
    Palīgfunkcija debug nolūkiem – atgriež visu
    EDOC iekšējo ierakstu nosaukumus.
    """
    edoc_file = Path(edoc_file)
    with zipfile.ZipFile(edoc_file, mode="r") as zf:
        for member in zf.infolist():
            yield member.filename
