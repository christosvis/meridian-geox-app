from geox_app.data import apply_mapping
import pandas as pd


def test_apply_mapping_renames_and_types():
    raw = pd.DataFrame(
        {
            "Day": ["2020-01-01", "2020-01-02"],
            "City": ["A", "B"],
            "KPI": ["1.5", "2.0"],
            "cost": ["10", "20"],
        }
    )
    raw.columns = raw.columns.str.lower()
    out = apply_mapping(
        raw,
        date_col="day",
        location_col="city",
        conversions_col="kpi",
        spend_col="cost",
    )
    assert list(out.columns)[:4] == ["date", "location", "conversions", "spend"]
    assert out["conversions"].dtype.kind == "f"
    assert str(out["location"].iloc[0]) == "A"
