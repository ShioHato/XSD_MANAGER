from __future__ import annotations

from pathlib import Path


def ensure_existing_file(path: str | Path) -> Path:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    return file_path

