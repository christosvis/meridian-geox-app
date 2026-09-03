"""Analysis window helpers. GeoX 1.0.0 has no cooldown field — extend end date."""

from __future__ import annotations

import pandas as pd


def cooldown_end(test_end: pd.Timestamp, cooldown_days: int) -> pd.Timestamp:
    end = pd.Timestamp(test_end).normalize()
    days = int(cooldown_days)
    if days < 0:
        raise ValueError("cooldown_days must be >= 0")
    if days == 0:
        return end
    return end + pd.Timedelta(days=days)


def window_label(*, include_cooldown: bool, cooldown_days: int) -> str:
    if include_cooldown and int(cooldown_days) > 0:
        return f"test_plus_{int(cooldown_days)}d_cooldown"
    return "test_only"
