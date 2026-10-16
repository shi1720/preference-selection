# Tariff Abolition and the Measurement of Trade-Agreement Use

Research manuscript by **Shivam Gupta**, 16 October 2026.

[Read the paper](paper/manuscript.pdf).

The study reconstructs preference-utilization statistics from official UK trade-regime
databases. UK exports to Switzerland show an increase from 44.26% to 61.21% in
2023–2024 even though agricultural utilization declines. A fixed-2023-basket
selection exercise gives a 54.91%–65.34% interval without changing claim assignments.
This is an accounting compatibility result, **not a causal estimate of learning or
the reform's realized effect**.

## Replicate

Python 3.12 and Tectonic are required to rebuild all outputs including the PDF.
From a clone of this repository:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python src/acquire.py
.venv/bin/python src/analyze.py
.venv/bin/python src/figures.py
.venv/bin/python src/report.py
.venv/bin/python -m unittest discover -s tests -v
cd paper
tectonic manuscript.tex
```

`acquire.py` verifies and re-extracts the archived vintage when the manifest exists;
it then needs no network. The statistical reproduction has no API key, paid data,
or model-service dependency. A fresh environment is recommended.

The seven test methods include 1,980 exhaustive rational bound configurations,
200 linear-programming cross-checks, 1,000 rational decomposition cases, raw-file
hash checks, year/quarantine checks, and independent published statistical controls.
The numerical cases verify mathematics and implementation; they are not empirical
trade observations. See [the saved verification log](results/verification.txt).

## Contents

- `data/raw/`: eight unchanged official ODS databases.
- `data/source_manifest.json`: exact URLs, hashes, byte sizes, extraction counts, and retrieval times.
- `data/processed/`: parsed tables, the retained panel, and the source-year quarantine.
- `src/`: acquisition, accounting methods, analysis, figures, and generated paper tables.
- `tests/`: independently formulated mathematical and source checks.
- `results/`: complete numerical outputs, including non-reversals and sensitivity results.
- `figures/`: six vector PDF figures and PNG versions.
- `paper/`: manuscript PDF, editable LaTeX source, and generated tables/macros.
- `docs/`: data definitions, literature positioning, commercial landscape, and limitations.

## Data vintage and interpretation

The eight workbooks were retrieved on 16 October 2026. They contain **55,754**
partner–chapter–year–direction records. The 2021 export workbook has **2,593** rows
whose declared Year is 2023. These remain in the raw archive and quarantine;
the analysis does not silently assign them to either year. The retained panel
therefore has **53,161** records. The Swiss case and the 2022–2024 broader comparisons
are unaffected by this screen.

No missing chapter is imputed as zero. Eligibility entry and exit are defined
on explicitly observed matched rows. The general-panel comparison requires at
least GBP 100 million in eligibility in both years, at least 99% matched coverage,
and positive common eligible support. Sixteen of 184 selected comparisons have
opposing aggregate/rate-component signs with changes of at least 0.5 percentage
point in each. The count is resolution- and sample-dependent.

Neither eligible trade nor unused eligible trade is a measure of duties paid or
commercially recoverable savings. HS2 rates do not isolate individual firm behavior.
The mixed-chapter bounds are sharp under the stated coarse information, not under
the full unobserved legal tariff-line allocation. No acceptance, publication,
causal identification, or exhaustive novelty certification is claimed.

## License and attribution

Code is provided under the MIT license. Official data remain under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
Contains public sector information licensed under the Open Government Licence v3.0.
Source: UK Department for Business and Trade, *Preference utilisation of UK trade
in goods*, 2021–2024 databases. The paper and original figures are copyright
Shivam Gupta, 2026; the code license does not relicense the paper or third-party data.

Suggested citation: Gupta, Shivam (2026). *Tariff Abolition and the Measurement of
Trade-Agreement Use*. Working paper. https://github.com/shi1720/preference-selection.
