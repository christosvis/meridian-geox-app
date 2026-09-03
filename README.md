# Meridian GeoX app

Streamlit workbench for [Google Meridian GeoX](https://developers.google.com/meridian/geox/intro-to-geox):
load a geo-day panel, design a single- or multi-cell test, then analyze lift (TBR).

Isolated env **`geox-app-venv`**. Do not add GeoX to marketing-ax Poetry or reuse
`meridian-venv` (MMM) / `geox-venv` (notebook sandbox).

## Setup

```bash
cd christos-analyses/meridian-geox-app
python3 -m venv geox-app-venv
source geox-app-venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python scripts/download_samples.py
```

`absl-py` is required at runtime even though PyPI lists it only under GeoX `dev`.

## Run

```bash
source geox-app-venv/bin/activate
streamlit run streamlit_app.py
```

Open http://localhost:8501. Load a Google sample on **Data**, then **Run design**
(explicit button — search is slow). Analysis needs a saved design plus a panel
that includes the test window.

## Pages

| Page | Role |
|------|------|
| Data | Sample CSVs or upload; map `date` / `location` / `conversions` / spend |
| Design | `run_design` — ranked candidates, quality checks, JSON |
| Analysis | TBR + optional cooldown window + Meridian ROI prior export |
| Compare | `compare_designs` and optional `concat_design_reports` |

**Compare vs concatenate:** Compare re-runs several `DesignConfig`s on the same
panel and ranks them. Concatenate only merges *already computed* `DesignSet`s
(e.g. last Design run + a comparison). Both live on Compare — concatenate is
not a separate workflow.

**SDID** is in the GeoX 1.0.0 enum (`Methodology.SDID`) but there is no estimator
(`methodology/sdid.py` is missing). The app always uses TBR.

**Cooldown:** GeoX `AnalysisConfig` has no cooldown field. The app extends
`analysis_end_date` so post-test days are still treated vs BAU control.

**Meridian priors:** Analysis exports iCPD, spend, and dates for
[CalibrationBuilder](https://developers.google.com/meridian/docs/advanced-modeling/set-custom-priors-past-experiments)
in **meridian-venv** (do not install `google-meridian` here). Holdback matches
Meridian’s zero-spend ROI estimand better than go-dark / heavy-up.

Interactive defaults use fewer candidates than the Colab (`n_candidates=5_000`
vs 100k) so a click finishes on a laptop. Expand **Search budget** for Colab-scale.

## Docs

- [Intro](https://developers.google.com/meridian/geox/intro-to-geox)
- [Design methodology](https://developers.google.com/meridian/geox/design-methodology)
- [TBR](https://developers.google.com/meridian/geox/counterfactual-modeling)
- [Inference](https://developers.google.com/meridian/geox/robust-inference)
- [Data validation and quality checks](https://developers.google.com/meridian/geox/data-validation-and-quality-checks)
- [Set custom ROI priors from experiments](https://developers.google.com/meridian/docs/advanced-modeling/set-custom-priors-past-experiments)
- Colabs: [single-cell](https://github.com/google/meridian-geox/blob/main/meridian_geox/colab/meridian_geox_single_cell_colab.ipynb), [multi-cell](https://github.com/google/meridian-geox/blob/main/meridian_geox/colab/meridian_geox_multicell_colab.ipynb)
