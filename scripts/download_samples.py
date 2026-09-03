"""Download Google GeoX example CSVs into data/samples/."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "samples"
BASE = (
    "https://raw.githubusercontent.com/google/meridian-geox/refs/heads/main/"
    "meridian_geox/data"
)
FILES = [
    "example_design_data_single_cell.csv",
    "example_analysis_data_single_cell_holdback.csv",
    "example_design_data_multi_cell_go_dark_heavy_up.csv",
    "example_analysis_data_multi_cell_go_dark_heavy_up.csv",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        url = f"{BASE}/{name}"
        df = pd.read_csv(url)
        path = OUT / name
        df.to_csv(path, index=False)
        print(f"  {path.name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
