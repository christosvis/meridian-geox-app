# Meridian GeoX app

Streamlit app for [Google Meridian GeoX](https://developers.google.com/meridian/geox/intro-to-geox):
load a geo-day panel, design a single- or multi-cell test, then analyze lift (TBR).


## Run

```bash
source geox-app-venv/bin/activate
streamlit run streamlit_app.py
```

Load a Google sample on **Data**, then **Run design**
(explicit button — search is slow). Analysis needs a saved design plus a panel
that includes the test window.

## Pages

| Page | Role |
|------|------|
| Data | Sample CSVs or upload; map `date` / `location` / `conversions` / spend |
| Design | `run_design` — ranked candidates, quality checks, JSON |
| Analysis | TBR + optional cooldown window + Meridian ROI prior export |
| Compare | `compare_designs` and optional `concat_design_reports` |


**Meridian priors:** Analysis exports iCPD, spend, and dates for
[CalibrationBuilder](https://developers.google.com/meridian/docs/advanced-modeling/set-custom-priors-past-experiments)
in **meridian-venv**. Holdback matches
Meridian’s zero-spend ROI estimand better than go-dark / heavy-up.

## Docs

- [Intro](https://developers.google.com/meridian/geox/intro-to-geox)
- [Design methodology](https://developers.google.com/meridian/geox/design-methodology)
- [TBR](https://developers.google.com/meridian/geox/counterfactual-modeling)
- [Inference](https://developers.google.com/meridian/geox/robust-inference)
- [Data validation and quality checks](https://developers.google.com/meridian/geox/data-validation-and-quality-checks)
- [Set custom ROI priors from experiments](https://developers.google.com/meridian/docs/advanced-modeling/set-custom-priors-past-experiments)
- Colabs: [single-cell](https://github.com/google/meridian-geox/blob/main/meridian_geox/colab/meridian_geox_single_cell_colab.ipynb), [multi-cell](https://github.com/google/meridian-geox/blob/main/meridian_geox/colab/meridian_geox_multicell_colab.ipynb)
