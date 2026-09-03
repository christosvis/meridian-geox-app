"""Build GeoX DesignConfig / Constraints and run design."""

from __future__ import annotations

import datetime as dt
from typing import Any

import meridian_geox as geox
import pandas as pd


def experiment_type(name: str) -> geox.ExperimentType:
    return geox.ExperimentType[name]


def assignment_rule(name: str) -> geox.GeoAssignmentRule:
    return geox.GeoAssignmentRule[name]


def parse_geo_set(text: str) -> set[str]:
    if not text or not text.strip():
        return set()
    return {part.strip() for part in text.replace("\n", ",").split(",") if part.strip()}


def parse_dates(text: str) -> set[pd.Timestamp]:
    geos = parse_geo_set(text)
    return {pd.Timestamp(x) for x in geos}


def build_design_config(
    *,
    duration_days: int,
    cell_types: dict[str, str],
    assignment: str,
    cpic: float | dict[str, float],
    design_output_count: int,
    alpha: float,
    power: float,
    n_candidates: int,
    n_ranked_candidates: int,
    min_r2: float,
    seed: int,
) -> geox.DesignConfig:
    types = {cell: experiment_type(kind) for cell, kind in cell_types.items()}
    kwargs: dict[str, Any] = {
        "experiment_duration": dt.timedelta(days=int(duration_days)),
        "experiment_types": types if len(types) > 1 else next(iter(types.values())),
        "methodology": geox.Methodology.TBR,
        "geo_assignment_rule": assignment_rule(assignment),
        "cell_count": len(types),
        "design_output_count": int(design_output_count),
        "alpha": float(alpha),
        "power": float(power),
        "n_candidates": int(n_candidates),
        "n_ranked_candidates": int(n_ranked_candidates),
        "min_r2": float(min_r2),
        "seed": int(seed),
        "test_type": geox.TestType.TWO_SIDED,
    }
    holdback = {
        cell: types[cell] == geox.ExperimentType.HOLDBACK for cell in types
    }
    if any(holdback.values()):
        if isinstance(cpic, dict):
            kwargs["cost_per_incremental_conversion"] = {
                cell: float(cpic.get(cell, 1.0))
                for cell, is_hb in holdback.items()
                if is_hb
            }
        else:
            kwargs["cost_per_incremental_conversion"] = float(cpic)
    return geox.DesignConfig(**kwargs)


def build_budget(kind: str, amount: float | None, pct: float | None) -> geox.Budget | None:
    if kind == "HOLDBACK":
        if amount is None:
            return None
        return geox.Budget(budget=float(amount))
    if pct is None:
        return None
    return geox.Budget(budget_pct=float(pct))


def build_constraints(
    *,
    excluded_geos: set[str],
    included_control_geos: set[str],
    excluded_dates: set[pd.Timestamp],
    budget_constraint: geox.Budget | dict[str, geox.Budget] | None,
    max_conversions_percent: float,
) -> geox.Constraints:
    kwargs: dict[str, Any] = {
        "excluded_geos": excluded_geos,
        "included_control_geos": included_control_geos,
        "excluded_dates": excluded_dates,
        "max_conversions_percent": float(max_conversions_percent),
    }
    if budget_constraint is not None:
        kwargs["budget_constraint"] = budget_constraint
    return geox.Constraints(**kwargs)


def run_design(
    data: pd.DataFrame,
    config: geox.DesignConfig,
    constraints: geox.Constraints,
    *,
    exclude_geos_no_response: bool,
    exclude_outlier_dates: bool,
) -> geox.DesignSet:
    quality = geox.QualityCheckConfig(
        exclude_geos_no_response=exclude_geos_no_response,
        exclude_outlier_dates=exclude_outlier_dates,
    )
    return geox.run_design(data, config, constraints, quality)


def assignment_table(design: geox.Design) -> pd.DataFrame:
    rows = []
    for geo in sorted(design.control_geos):
        rows.append({"location": geo, "group": "control", "cell": ""})
    for cell, per in design.designs.items():
        for geo in sorted(per.treatment_geos):
            rows.append({"location": geo, "group": "treatment", "cell": cell})
    for geo in sorted(design.excluded_geos):
        rows.append({"location": geo, "group": "excluded", "cell": ""})
    return pd.DataFrame(rows)
