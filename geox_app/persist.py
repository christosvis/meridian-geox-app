"""Save and load Design JSON under outputs/designs/."""

from __future__ import annotations

import pickle
import re
from pathlib import Path

import meridian_geox as geox

ROOT = Path(__file__).resolve().parent.parent
LIBRARY_DIR = ROOT / "outputs" / "designs"
LATEST_NAME = "_latest.json"


def _slug(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    slug = slug.strip("._") or "design"
    if slug in {"_latest", "latest"}:
        slug = "design"
    return slug


def ensure_library() -> Path:
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    return LIBRARY_DIR


def save_design(design: geox.Design, name: str) -> Path:
    ensure_library()
    path = LIBRARY_DIR / f"{_slug(name)}.json"
    payload = design.export_to_json()
    path.write_text(payload, encoding="utf-8")
    (LIBRARY_DIR / LATEST_NAME).write_text(payload, encoding="utf-8")
    return path


def save_latest(design: geox.Design) -> Path:
    ensure_library()
    path = LIBRARY_DIR / LATEST_NAME
    path.write_text(design.export_to_json(), encoding="utf-8")
    return path


ANALYSIS_DIR = ROOT / "outputs" / "analysis"


def save_analysis_pickle(result: geox.AnalysisResult, name: str = "_latest") -> Path:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    path = ANALYSIS_DIR / f"{name}.pkl"
    path.write_bytes(pickle.dumps(result, protocol=pickle.HIGHEST_PROTOCOL))
    return path


def list_saved_designs() -> list[Path]:
    if not LIBRARY_DIR.exists():
        return []
    return sorted(
        p for p in LIBRARY_DIR.glob("*.json") if p.name != LATEST_NAME
    )


def latest_path() -> Path | None:
    path = LIBRARY_DIR / LATEST_NAME
    return path if path.exists() else None


def load_design(path: Path) -> geox.Design:
    return geox.Design.load_from_json(path.read_text(encoding="utf-8"))
