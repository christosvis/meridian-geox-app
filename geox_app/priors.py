"""Export GeoX analysis lift/iCPD into Meridian CalibrationBuilder inputs.

Does not import google-meridian. meridian-app stays on meridian-venv.
https://developers.google.com/meridian/docs/advanced-modeling/set-custom-priors-past-experiments
"""

from __future__ import annotations

import json
from typing import Any

import meridian_geox as geox
import pandas as pd

PRIORS_DOCS = (
    "https://developers.google.com/meridian/docs/advanced-modeling/"
    "set-custom-priors-past-experiments"
)


def _est(est: geox.Estimate | None) -> dict[str, float] | None:
    if est is None:
        return None
    return {
        "point_estimate": float(est.point_estimate),
        "standard_deviation": float(est.standard_deviation),
        "lower_bound": float(est.lower_bound),
        "upper_bound": float(est.upper_bound),
        "p_value": float(est.p_value),
    }


def experiment_payload(
    result: geox.AnalysisResult,
    *,
    window: str,
    channel_name: str = "geo_experiment_channel",
) -> dict[str, Any]:
    cfg = result.analysis_config
    start = pd.Timestamp(cfg.analysis_start_date).date().isoformat()
    end = pd.Timestamp(cfg.analysis_end_date).date().isoformat()
    cells = []
    for cell, metrics in result.results.items():
        spend = None
        if metrics.descriptive_metrics is not None:
            spend = metrics.descriptive_metrics.estimated_bau_spend
            if spend is not None:
                spend = float(spend)
        cells.append(
            {
                "cell_id": cell,
                "channel_name": channel_name if len(result.results) == 1 else f"{channel_name}_{cell}",
                "icpd": _est(metrics.icpd),
                "lift": _est(metrics.lift),
                "percent_lift": _est(metrics.percent_lift),
                "estimated_bau_spend": spend,
                "analysis_start_date": start,
                "analysis_end_date": end,
            }
        )
    return {
        "source": "meridian_geox",
        "geox_version": "1.0.0",
        "window": window,
        "docs": PRIORS_DOCS,
        "notes": [
            "CalibrationBuilder.with_meridian_geox_experiment_result reads icpd "
            "point/sd, estimated_bau_spend, and analysis dates from AnalysisResult.",
            "Use with_incrementality_experiment_result in meridian-venv if that "
            "env does not install meridian-geox.",
            "Holdback (new spend vs zero in control) matches Meridian’s "
            "zero-spend ROI estimand better than go-dark / heavy-up (marginal).",
            "iCPD is incremental KPI per euro of experiment spend; it equals "
            "Meridian ROI when the KPI is revenue.",
        ],
        "cells": cells,
    }


def calibration_snippet(payload: dict[str, Any]) -> str:
    lines = [
        "from meridian.model.prior_calibration import CalibrationBuilder",
        "",
        f"# Docs: {PRIORS_DOCS}",
        "builder = CalibrationBuilder(meridian_model)  # your fitted/unfitted Meridian",
    ]
    for cell in payload["cells"]:
        icpd = cell.get("icpd")
        if not icpd:
            lines.append(
                f"# {cell['cell_id']}: no iCPD (need spend on the analysis panel)."
            )
            continue
        spend = cell["estimated_bau_spend"]
        spend_repr = "None" if spend is None else repr(spend)
        lines.extend(
            [
                "",
                f"# {cell['cell_id']}",
                "builder = builder.with_incrementality_experiment_result(",
                f"    channel={cell['channel_name']!r},",
                f"    point_estimate={icpd['point_estimate']!r},",
                f"    standard_error={icpd['standard_deviation']!r},",
                f"    spend={spend_repr},",
                f"    start_date={cell['analysis_start_date']!r},",
                f"    end_date={cell['analysis_end_date']!r},",
                ")",
            ]
        )
    lines.extend(
        [
            "",
            "# If this AnalysisResult pickle was dumped with meridian-geox 1.0.0:",
            "# builder = builder.with_meridian_geox_experiment_result(",
            "#     channel='paid_search', analysis_result=loaded_result)",
            "calibrated = builder.build()",
        ]
    )
    return "\n".join(lines) + "\n"


def payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2)


def cells_frame(payload: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for cell in payload["cells"]:
        icpd = cell.get("icpd") or {}
        lift = cell.get("lift") or {}
        rows.append(
            {
                "cell_id": cell["cell_id"],
                "channel_name": cell["channel_name"],
                "window": payload["window"],
                "start": cell["analysis_start_date"],
                "end": cell["analysis_end_date"],
                "icpd_point": icpd.get("point_estimate"),
                "icpd_sd": icpd.get("standard_deviation"),
                "lift_point": lift.get("point_estimate"),
                "estimated_bau_spend": cell.get("estimated_bau_spend"),
            }
        )
    return pd.DataFrame(rows)
