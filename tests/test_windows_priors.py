from __future__ import annotations

import pandas as pd

from geox_app.priors import calibration_snippet
from geox_app.windows import cooldown_end, window_label


def test_cooldown_end_zero():
    assert cooldown_end("2020-04-30", 0) == pd.Timestamp("2020-04-30")


def test_cooldown_end_adds_days():
    assert cooldown_end("2020-04-30", 7) == pd.Timestamp("2020-05-07")


def test_window_label():
    assert window_label(include_cooldown=False, cooldown_days=14) == "test_only"
    assert window_label(include_cooldown=True, cooldown_days=14) == "test_plus_14d_cooldown"


def test_calibration_snippet_mentions_channel():
    payload = {
        "cells": [
            {
                "cell_id": "cell_1",
                "channel_name": "uac",
                "icpd": {"point_estimate": 1.2, "standard_deviation": 0.3},
                "estimated_bau_spend": 1000.0,
                "analysis_start_date": "2020-04-01",
                "analysis_end_date": "2020-04-30",
            }
        ]
    }
    text = calibration_snippet(payload)
    assert "uac" in text
    assert "with_incrementality_experiment_result" in text
    assert "geox-app-venv" not in text
