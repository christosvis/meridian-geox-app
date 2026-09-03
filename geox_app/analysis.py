"""Run GeoX analysis and flatten estimates for display."""

from __future__ import annotations

import meridian_geox as geox
import pandas as pd


def estimate_frame(metrics: geox.AnalysisMetrics) -> pd.DataFrame:
    rows = []
    for name, est in (
        ("lift", metrics.lift),
        ("percent_lift", metrics.percent_lift),
        ("icpd", metrics.icpd),
    ):
        if est is None:
            continue
        rows.append(
            {
                "metric": name,
                "point": est.point_estimate,
                "ci_low": est.lower_bound,
                "ci_high": est.upper_bound,
                "sd": est.standard_deviation,
                "p_value": est.p_value,
                "ci_includes_zero": est.lower_bound <= 0 <= est.upper_bound,
            }
        )
    return pd.DataFrame(rows)


def run_analysis(
    data: pd.DataFrame,
    design: geox.Design,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    pretest_end: pd.Timestamp | None,
    exclude_outlier_dates: bool,
    n_placebo_candidates: int,
    n_top_placebos: int,
) -> geox.AnalysisResult:
    config = analysis_config(
        design,
        start=start,
        end=end,
        pretest_end=pretest_end,
        n_placebo_candidates=n_placebo_candidates,
        n_top_placebos=n_top_placebos,
    )
    quality = geox.QualityCheckConfig(
        exclude_geos_no_response=True,
        exclude_outlier_dates=exclude_outlier_dates,
    )
    return geox.analyze(data, config, quality)


def analysis_config(
    design: geox.Design,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    pretest_end: pd.Timestamp | None,
    n_placebo_candidates: int,
    n_top_placebos: int,
) -> geox.AnalysisConfig:
    return geox.AnalysisConfig(
        design=design,
        analysis_start_date=pd.Timestamp(start),
        analysis_end_date=pd.Timestamp(end),
        pretest_end_date=pd.Timestamp(pretest_end) if pretest_end is not None else None,
        n_placebo_candidates=int(n_placebo_candidates),
        n_top_placebos=int(n_top_placebos),
    )


def preview_analysis_quality(
    data: pd.DataFrame,
    config: geox.AnalysisConfig,
    *,
    exclude_outlier_dates: bool,
) -> geox.QualityCheckResult:
    quality = geox.QualityCheckConfig(
        exclude_geos_no_response=True,
        exclude_outlier_dates=exclude_outlier_dates,
    )
    return geox.check_analysis_data_quality(data, config, quality)
