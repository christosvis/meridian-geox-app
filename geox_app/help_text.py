"""User-facing copy: experiment types, CpIC, widget help."""

from __future__ import annotations

TYPES_OF_EXPERIMENTS_URL = (
    "https://developers.google.com/meridian/geox/types-of-experiments"
)

STUDY_TYPE_HELP = {
    "single": (
        "One treatment group vs one control. Google’s default for a single "
        "channel or tactic: all power goes to one comparison, so you typically "
        "need fewer geos and less budget for a given MDE."
    ),
    "multi": (
        "Several treatment arms vs a **shared** control. Use when you need the "
        "same market conditions for budget-level tests (e.g. go-dark + heavy-up), "
        "cross-publisher comparison, or tactic A/B. Needs more geos and budget "
        "or MDE gets worse."
    ),
}

INTERVENTION = {
    "HOLDBACK": {
        "label": "Holdback",
        "summary": (
            "New spend in **treatment**; **control** is held back (zero / no new "
            "campaign). For net-new channels, tactics, or accounts — prove "
            "incremental return before scaling."
        ),
        "setup": "Treatment: gets new spend. Control: held back or zero spend.",
    },
    "GO_DARK": {
        "label": "Go-dark",
        "summary": (
            "Shut off (or fully ablate) **existing** spend in **treatment**; "
            "**control** stays business-as-usual. For defending live budgets "
            "(what you lose if ads go off)."
        ),
        "setup": "Treatment: spend ablated. Control: BAU spend.",
    },
    "HEAVY_UP": {
        "label": "Heavy-up",
        "summary": (
            "Add incremental spend in **treatment**; **control** stays BAU. For "
            "marginal returns on an established channel, or when current spend "
            "is too low to power a go-dark test."
        ),
        "setup": "Treatment: increased spend (+X%). Control: BAU spend.",
    },
}

CPIC_FEASIBILITY = """
**Evaluating design feasibility (design implied CpIC)**

Compare **implied CpIC** against your **expected CpIC** to check the experiment
is adequately powered.

- If implied CpIC **<** expected CpIC, the test is underpowered (unlikely to
  detect lift). Increase budget or test duration.
- If implied CpIC **≥** expected CpIC, the test is adequately powered.

For a **holdback** study, design implied CpIC equals your input CpIC.
""".strip()

ASSIGNMENT_HELP = (
    "Stratified sampling clusters geos on KPI shape (volume, trend, seasonality) "
    "then assigns inside clusters — Google’s default. Random assignment skips "
    "clustering; only use it when you have very few geos."
)


QUALITY_CHECKS_URL = (
    "https://developers.google.com/meridian/geox/data-validation-and-quality-checks"
)

QUALITY_INTRO = """
**Validation** (hard fail): schema, daily grain, conversions > 0, pretest ≥ 3×
duration, enough geos, spend columns for go-dark/heavy-up, CpIC > 0 for
holdback, `max_conversions_percent` < 0.5. These raise `ValueError` and stop
the run.

**Quality** (warnings): spend with no conversions, missing-day share, too many
zero-conversion days, >500 geos, duplicate geo-dates, outlier pretest dates,
budget-type mismatches. Thresholds (30% missing days, 500 geos) are hardcoded
in GeoX and cannot be changed.

[Data validation and quality checks](https://developers.google.com/meridian/geox/data-validation-and-quality-checks)
""".strip()


PRIORS_DOCS = (
    "https://developers.google.com/meridian/docs/advanced-modeling/"
    "set-custom-priors-past-experiments"
)

SDID_NOTE = (
    "**SDID** is on `Methodology` in GeoX 1.0.0 (`SDID = 2`) but there is no "
    "`sdid.py` estimator — only TBR is implemented. This app always sets "
    "`methodology=TBR`."
)


def intervention_help(kind: str) -> str:
    spec = INTERVENTION[kind]
    return f"{spec['summary']} {spec['setup']}"
