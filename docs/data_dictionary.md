# Data and estimands

Each retained observation is a partner ISO code × HS2 chapter × release year ×
UK trade direction. A partner in a database can have no preference-eligible trade.

The panel's value fields are numeric GBP, not formatted strings. `eligible` and
`used` are the official preference-eligible and preference-use values. `unused`
is their difference. `normal` excludes special processing; `unknown` is the
unknown-regime component. `mfn_zero`, `fta_zero`, and `scheme_zero` distinguish
routes to duty-free treatment. `fta_positive` and `scheme_positive` can count
as preference use without constituting zero-duty treatment.

`source_file_year` and `declared_year` are preserved separately. Only matching
years enter `panel.csv`. `quarantined_year_mismatches.csv` preserves every
inconsistent row. ISO `NA` means Namibia and must not be converted to a missing value.

## Outputs

`partner_statistics.csv` contains eligible totals, use, unused value, PUR and
the duty-free share, together with completeness counts. Unknown/processing
entries are excluded according to the stated statistic, not by deleting their
whole partner row.

`decompositions.csv` contains each valid matched pair's aggregate change, rate,
weight, entry, and exit components in **rate units**: multiply by 100 to obtain
percentage points. Weights are normalized within common eligible support. File
coverage columns give matched eligibility divided by all eligibility reported
for that partner/direction/year. The unmatched remainder is not called policy exit.

`material_panels.csv` applies the primary GBP 100m/99%-coverage screen for
2022–2023 and 2023–2024. A material reversal requires opposite signs and both
changes at least 0.005 in rate units. Its rows are not independent samples.

`swiss_groups.csv` contains all chapters; agricultural chapters 01–24; certain
industrial-removal chapters 25–97 excluding 35 and 38; and the mixed pool 35/38.
It keeps those groups separate rather than labeling all 25–97 agriculture-free.

`swiss_retention_bounds.csv` and `swiss_retention_curve.csv` implement the
paper's fixed-basket benchmark. No quantity, value, or claim changes are modeled.
The benchmark is deliberately not named a causal effect. Realized 2024 trade
is not a measure of retained 2023 mixed-chapter value.

Other files supply complete threshold, aggregation, weighting, and leave-one-out
checks. Every figure and paper table is built from these outputs.

## Source conditions

Official data collection:
https://www.gov.uk/government/collections/preference-utilisation-of-uk-trade-in-goods

All eight release pages and exact download links are in `data/source_manifest.json`.
The official technical annex explains reporting and denominator conventions.
The 2021 import series has a staged-customs-controls comparability limitation;
the broad comparative exercise starts in 2022. Export partner coverage varies
with data-exchange availability, so the panel is not all UK exports.

For a revised source vintage, preserve a separate archive and manifest, and
rerun the source-year and published-control tests before drawing comparisons.
