"""Generate LaTeX tables and numeric macros from saved estimates."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';P=ROOT/'paper'

def pct(v):return f'{100*v:.2f}'
def pp(v):return f'{100*v:+.2f}'
def million(v):return f'{v/1e6:,.2f}'
def table(name,caption,label,columns,header,rows,note):
    text='\\begin{table}[!htbp]\n\\centering\n\\caption{'+caption+'}\\label{'+label+'}\n'
    text+='\\small\n\\begin{tabular}{'+columns+'}\n\\toprule\n'+header+' \\\\\n\\midrule\n'
    text+='\n'.join(' & '.join(str(v) for v in row)+' \\\\' for row in rows)
    text+='\n\\bottomrule\n\\end{tabular}\n\\par\\vspace{3pt}\\begin{minipage}{.97\\linewidth}\\footnotesize '+note+'\\end{minipage}\n\\end{table}\n'
    (P/name).write_text('\n'.join(line.rstrip() for line in text.splitlines())+'\n')

def main():
    s=json.loads((R/'summary.json').read_text());a=pd.read_csv(R/'data_audit.csv')
    table('table_coverage.tex','Source coverage and the year-consistency screen','tab:coverage','llrrrr',
        'Year & Direction & Source rows & Quarantined & Retained & Partners',
        [[z.year,z.direction,f'{z.source_rows:,}',f'{z.quarantined_year_mismatches:,}',f'{z.rows:,}',z.partners] for z in a.itertuples()],
        'Partner counts refer to retained records and include partners with no positive eligibility. The 2021 export workbook has 2,593 records whose Year field says 2023. These records are archived but excluded. All other records pass the file-year check. Source: DBT databases retrieved on 16 October 2026 and calculations.')
    g=pd.read_csv(R/'swiss_groups.csv');sw=[]
    for y in range(2021,2025):
        z=g[(g.year==y)&(g.group=='All chapters')].iloc[0];b=g[(g.year==y)&(g.group=='Agriculture 01-24')].iloc[0]
        sw.append([y,million(z.eligible),million(z.used),pct(z.pur),million(b.eligible),pct(b.pur),pct(z.duty_free)])
    table('table_swiss.tex','UK exports to Switzerland: eligibility, use, and duty-free access','tab:swiss','lrrrrrr',
        ' & \\multicolumn{3}{c}{All chapters} & \\multicolumn{2}{c}{Chapters 01--24} & Duty-free \\\\ \nYear & Eligible & Used & PUR (\\%) & Eligible & PUR (\\%) & share (\\%)',sw,
        'Values are GBP million at each year\'s prices and conversion rate. Duty-free access uses known normal-regime trade, excludes special processing and unknown regimes, and combines MFN-zero and preferential-zero entries. It is not a measure of non-tariff barriers or a welfare index. The Swiss series passes the year-consistency screen in every year.')
    d=pd.read_csv(R/'decompositions.csv');rows=[]
    for y in [2021,2022,2023]:
        z=d[(d.iso=='CH')&(d.direction=='exports')&(d.year0==y)].iloc[0]
        rows.append([f'{y}--{str(y+1)[-2:]}',*[pp(z[k]) for k in ['change','rate','weight','exit','entry']]])
    z=s['swiss_agri'];rows.append(['2023--24, 01--24',*[pp(z[k]) for k in ['change','rate','weight','exit','entry']]])
    table('table_decomposition.tex','Changes in Swiss-market utilization, in percentage points','tab:decomposition','lrrrrr',
        'Period & Total & Rates & Weights & Exit & Entry',rows,
        'Rates and weights are normalized on common eligible support. Exit and entry are exact accounting adjustments for aggregate cells changing eligibility status. Rates include within-chapter product and firm composition. The entries are not causal effects. Components use unrounded values; displayed sums can differ by 0.01 percentage point.')
    b=pd.read_csv(R/'swiss_retention_bounds.csv')
    table('table_bounds.tex','Frozen-basket utilization after industrial tariff abolition','tab:bounds','lrrrr',
        'Base year & Observed PUR & Lower bound & Upper bound & Minimum increase',
        [[int(z.base_year),pct(z.base_pur),pct(z.lower),pct(z.upper),pp(z.minimum_mechanical_change)] for z in b.itertuples()],
        'All entries are percentages or percentage-point changes. Retain chapters 01--24, remove chapters 25--97 except 35 and 38, and allow any used/unused split of retained eligibility within the two mixed chapters. These are sharp accounting bounds under that information set. They are not bounds on the realized causal effect of reform. The observed 2024 PUR is 61.21\\%.')
    z=pd.read_csv(R/'material_panels.csv');rows=[]
    for iso,direction,y in [('CH','exports',2023),('PL','exports',2022),('MK','exports',2022),('MT','exports',2022),('CA','exports',2023),('CR','imports',2022)]:
        q=z[(z.iso==iso)&(z.direction==direction)&(z.year0==y)].iloc[0]
        rows.append([iso,direction,f'{y}--{str(y+1)[-2:]}',*[pp(q[k]) for k in ['change','rate','weight','exit']]])
    table('table_examples.tex','Largest material sign reversals in the eligible panel','tab:examples','lllrrrr',
        'Partner & Direction & Period & Total & Rates & Weights & Exit',rows,
        'Percentage points. CH: Switzerland; PL: Poland; MK: North Macedonia; MT: Malta; CA: Canada; CR: Costa Rica. These six panels have the largest absolute total changes among material reversals. All displayed entry contributions round to zero except Poland (2022--23), at +0.03 pp. Direction refers to UK trade. The full file includes all eligible panels, including non-reversals.')
    z=pd.read_csv(R/'panel_sensitivity.csv');z=z[z.threshold_pp==.5]
    table('table_sensitivity.tex','Sensitivity of the descriptive reversal count','tab:sensitivity','rrrr',
        'Eligibility cutoff & Panels & Reversals & Share (\\%)',
        [[f'\\pounds{z.cutoff_million:.0f}m',z.panels,z.reversals,f'{100*z.reversals/z.panels:.1f}'] for z in z.itertuples()],
        'Both years must meet the eligibility cutoff. All panels are partner--direction--year-pair observations for 2022--23 or 2023--24, have at least 99\\% matched eligibility coverage in each year, and have a common eligible support. A material reversal requires opposite signs and magnitudes of at least 0.5 pp for both the aggregate change and the within-chapter rate component. Repeated partners are not independent observations.')
    # Precision is set once here; manuscript numbers reference these macros.
    lo=b[b.base_year==2023].iloc[0];sw0=g[(g.year==2023)&(g.group=='All chapters')].iloc[0];sw1=g[(g.year==2024)&(g.group=='All chapters')].iloc[0]
    vals={'RawRows':f"{s['source_rows']:,}",'PanelRows':f"{s['rows']:,}",'QuarantineRows':f"{s['quarantined_year_mismatches']:,}",
        'SwissBefore':pct(sw0.pur),'SwissAfter':pct(sw1.pur),'SwissChange':pct(sw1.pur-sw0.pur),
        'LowerBound':pct(lo.lower),'UpperBound':pct(lo.upper),'MinSelection':pct(lo.minimum_mechanical_change),
        'AgriChange':pct(s['swiss_agri']['change']),'AgriRate':pct(s['swiss_agri']['rate']),
        'PanelCount':str(s['material_panels']),'ReversalCount':str(s['material_reversals']),
        'EligibleFall':pct(1-sw1.eligible/sw0.eligible),'UnusedBefore':million(sw0.unused),'UnusedAfter':million(sw1.unused)}
    (P/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in vals.items())+'\n')

if __name__=='__main__':main()
