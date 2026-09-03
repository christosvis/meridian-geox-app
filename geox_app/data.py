"""Load Google sample CSVs and map columns to the GeoX schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = ROOT / "data" / "samples"

SAMPLE_FILES = {
    "single_design": "example_design_data_single_cell.csv",
    "single_analysis": "example_analysis_data_single_cell_holdback.csv",
    "multi_design": "example_design_data_multi_cell_go_dark_heavy_up.csv",
    "multi_analysis": "example_analysis_data_multi_cell_go_dark_heavy_up.csv",
}

SAMPLE_URL = (
    "https://raw.githubusercontent.com/google/meridian-geox/refs/heads/main/"
    "meridian_geox/data/{name}"
)

CANONICAL = ("date", "location", "conversions")


def sample_path(kind: str) -> Path:
    return SAMPLE_DIR / SAMPLE_FILES[kind]


def load_sample(kind: str) -> pd.DataFrame:
    path = sample_path(kind)
    if not path.exists():
        df = pd.read_csv(SAMPLE_URL.format(name=SAMPLE_FILES[kind]))
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        return _normalize_raw(df)
    return _normalize_raw(pd.read_csv(path))


def load_csv(file: Any) -> pd.DataFrame:
    return _normalize_raw(pd.read_csv(file))


def _normalize_raw(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = out.columns.astype(str).str.strip().str.lower()
    return out


def guess_column(columns: list[str], *candidates: str) -> str | None:
    lower = {c: c for c in columns}
    for name in candidates:
        if name in lower:
            return name
    return None


def apply_mapping(
    df: pd.DataFrame,
    *,
    date_col: str,
    location_col: str,
    conversions_col: str,
    spend_col: str | None = None,
    spend_cell_cols: dict[str, str] | None = None,
) -> pd.DataFrame:
    rename: dict[str, str] = {
        date_col: "date",
        location_col: "location",
        conversions_col: "conversions",
    }
    if spend_col:
        rename[spend_col] = "spend"
    if spend_cell_cols:
        for cell, src in spend_cell_cols.items():
            if src:
                rename[src] = f"spend_{cell}"

    out = df.rename(columns=rename).copy()
    numeric = ["conversions"]
    if "spend" in out.columns:
        numeric.append("spend")
    numeric.extend(
        c for c in out.columns if c.startswith("spend_cell_")
    )
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["location"] = out["location"].astype(str)
    return out


def panel_summary(df: pd.DataFrame) -> dict[str, Any]:
    n_geo = df["location"].nunique()
    n_dates = df["date"].nunique()
    expected = n_geo * n_dates
    missing = expected - len(df.drop_duplicates(["location", "date"]))
    return {
        "rows": len(df),
        "geos": n_geo,
        "dates": n_dates,
        "start": df["date"].min(),
        "end": df["date"].max(),
        "duplicate_or_gap_vs_full_grid": missing,
        "conversion_nulls": int(df["conversions"].isna().sum()),
    }
