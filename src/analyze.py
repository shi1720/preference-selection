"""Reproduce all paper estimates and tables from archived official databases."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from methods import decompose,retention_bounds,fixed_retention_bounds

ROOT=Path(__file__).resolve().parents[1]

def load():
    parts=[]
    for year in range(2021,2025):
        for direction in ['imports','exports']:
            x=pd.read_csv(ROOT/'data/processed'/f'{year}_{direction}.csv',dtype=str,keep_default_na=False)
            out=x[['Partner ISO','Partner name','Agreement','HS2','HS2 description','Agri flag','HS section']].copy()
            out.columns=['iso','partner','agreement','hs2','description','agri','section']
            mapping={'total':f'Total {direction} (£)','normal':f'Total {direction} excl. special processing (£)',
                'mfn_zero':f'MFN zero {direction} (£)','mfn_positive':f'MFN non-zero {direction} (£)',
                'eligible':f'Pref eligible {direction} (£)','used':f'Pref usage {direction} (£)',
                'fta_zero':f'FTA zero {direction} (£)','fta_positive':f'FTA non-zero {direction} (£)',
                'special':f'Special processing {direction} (£)','unknown':f'Unknown {direction} (£)'}
            for k,c in mapping.items():out[k]=pd.to_numeric(x[c],errors='coerce')
            scheme=[c for c in x if ('GSP' in c or 'DCTS' in c) and 'non-zero' not in c and ' zero ' in c]
            scheme_pos=[c for c in x if ('GSP' in c or 'DCTS' in c) and 'non-zero' in c]
            out['scheme_zero']=pd.to_numeric(x[scheme[0]],errors='coerce') if scheme else 0.
            out['scheme_positive']=pd.to_numeric(x[scheme_pos[0]],errors='coerce') if scheme_pos else 0.
            out['source_file_year']=year
            out['declared_year']=pd.to_numeric(x['Year'],errors='coerce')
            out['year']=year;out['direction']=direction
            out['hs2']=out.hs2.str.zfill(2)
            out['unused']=out.eligible-out.used
            parts.append(out)
    x=pd.concat(parts,ignore_index=True)
    bad=x.source_file_year!=x.declared_year
    x.loc[bad].to_csv(ROOT/'data/processed/quarantined_year_mismatches.csv',index=False)
    x=x.loc[~bad].copy()
    if x.duplicated(['iso','hs2','year','direction']).any():raise ValueError('Duplicate cell key')
    x.to_csv(ROOT/'data/processed/panel.csv',index=False)
    return x

def stats(z):
    # Missing components are never silently converted to zeros. Aggregate only complete
    # rows for the specific statistic; counts and excluded total value are exported.
    ep=z.dropna(subset=['eligible','used']);e=ep.eligible.sum();p=ep.used.sum()
    known=z.dropna(subset=['normal','unknown','mfn_zero','fta_zero','scheme_zero'])
    k=known.normal.sum()-known.unknown.sum()
    return dict(cells=len(z),eligible_cells=len(ep),total=float(z.total.sum()),
        eligible=float(e),used=float(p),unused=float(e-p),pur=float(p/e) if e else None,
        known_normal=float(k),duty_free=float((known.mfn_zero+known.fta_zero+known.scheme_zero).sum()/k) if k else None,
        mfn_zero=float(known.mfn_zero.sum()),preference_zero=float((known.fta_zero+known.scheme_zero).sum()),
        missing_ep_cells=int(len(z)-len(ep)),missing_ep_total=float(z.loc[~z.index.isin(ep.index),'total'].sum()))

def paired(x,iso,direction,y0,y1,chapters=None):
    z=x[(x.iso==iso)&(x.direction==direction)]
    if chapters is not None:z=z[z.hs2.isin(chapters)]
    # Inner join: a missing country/chapter row is not declared to be a true zero.
    z=z[z.year==y0].merge(z[z.year==y1],on=['iso','hs2'],suffixes=('0','1'))
    z=z.dropna(subset=['eligible0','eligible1','used0','used1'])
    if not len(z) or z.eligible0.sum()==0 or z.eligible1.sum()==0:return None
    try:r=decompose(z.eligible0,z.used0,z.eligible1,z.used1)
    except ValueError:return None
    r.update(iso=iso,direction=direction,year0=y0,year1=y1,matched_cells=len(z),
        pur0=z.used0.sum()/z.eligible0.sum(),pur1=z.used1.sum()/z.eligible1.sum())
    if abs(r['residual'])>1e-10:raise AssertionError(r)
    return r

def main():
    x=load();out=ROOT/'results'
    audit=[]
    for (year,direction),z in x.groupby(['year','direction']):
        complete=z.dropna(subset=['eligible','used'])
        manifest=json.loads((ROOT/'data/source_manifest.json').read_text())
        source_rows=next(m['rows'] for m in manifest if m['year']==year and m['direction']==direction)
        a=dict(year=int(year),direction=direction,source_rows=source_rows,
            quarantined_year_mismatches=source_rows-len(z),rows=len(z),partners=z.iso.nunique(),
            missing_eligible=int(z.eligible.isna().sum()),missing_used=int(z.used.isna().sum()),
            used_exceeds_eligible=int((complete.used>complete.eligible).sum()),
            negative_values=int((z.select_dtypes('number').drop(columns='year') < 0).sum().sum()))
        audit.append(a)
    pd.DataFrame(audit).to_csv(out/'data_audit.csv',index=False)
    aggregate=[]
    for (year,direction,iso),z in x.groupby(['year','direction','iso']):
        aggregate.append(dict(year=int(year),direction=direction,iso=iso,partner=z.partner.iloc[0],**stats(z)))
    aggregate=pd.DataFrame(aggregate);aggregate.to_csv(out/'partner_statistics.csv',index=False)
    decomps=[]
    for direction in ['imports','exports']:
        for iso in sorted(x[x.direction==direction].iso.unique()):
            for y0,y1 in [(2021,2022),(2022,2023),(2023,2024)]:
                r=paired(x,iso,direction,y0,y1)
                if r is not None:
                    # Export coverage shares make the matched-universe restriction visible.
                    for t,y in [(0,y0),(1,y1)]:
                        den=x[(x.iso==iso)&(x.direction==direction)&(x.year==y)].eligible.sum()
                        r[f'eligible_coverage{t}']=r[f'eligible{t}']/den if den else np.nan
                    decomps.append(r)
    dec=pd.DataFrame(decomps);dec.to_csv(out/'decompositions.csv',index=False)
    ch=x[(x.iso=='CH')&(x.direction=='exports')]
    groups=[]
    for year,z in ch.groupby('year'):
        h=pd.to_numeric(z.hs2)
        for group,mask in [('All chapters',h.between(1,99)),('Agriculture 01-24',h.between(1,24)),
            ('Certain exit 25-97 excl 35,38',h.between(25,97)&~h.isin([35,38])),
            ('Mixed chapters 35,38',h.isin([35,38]))]:
            groups.append(dict(year=int(year),group=group,**stats(z[mask])))
    groups=pd.DataFrame(groups);groups.to_csv(out/'swiss_groups.csv',index=False)
    bounds=[]
    for y0 in [2021,2022,2023]:
        base=ch[ch.year==y0];h=pd.to_numeric(base.hs2)
        s=stats(base[h.between(1,24)]);a=stats(base[h.isin([35,38])]);all_s=stats(base)
        lo,hi=retention_bounds(s['eligible'],s['used'],a['eligible'],a['used'])
        benchmark=(s['used']+a['used'])/(s['eligible']+a['eligible'])
        bounds.append(dict(base_year=y0,base_pur=all_s['pur'],lower=lo,upper=hi,
            retained_agri_rate=s['pur'],certain_exit_only=benchmark,
            minimum_mechanical_change=lo-all_s['pur'],maximum_mechanical_change=hi-all_s['pur'],
            observed_2024=stats(ch[ch.year==2024])['pur']))
    pd.DataFrame(bounds).to_csv(out/'swiss_retention_bounds.csv',index=False)
    ch0=groups[(groups.year==2023)&(groups.group=='Agriculture 01-24')].iloc[0]
    ca=groups[(groups.year==2023)&(groups.group=='Mixed chapters 35,38')].iloc[0]
    curve=[]
    for r in np.linspace(0,ca.eligible,201):
        lo,hi=fixed_retention_bounds(ch0.eligible,ch0.used,ca.eligible,ca.used,r)
        curve.append(dict(retained_million=r/1e6,lower=lo,upper=hi))
    pd.DataFrame(curve).to_csv(out/'swiss_retention_curve.csv',index=False)
    agri=[str(i).zfill(2) for i in range(1,25)]
    sr=paired(x,'CH','exports',2023,2024,agri)
    (out/'swiss_agri_decomposition.json').write_text(json.dumps(sr,indent=2)+'\n')
    # Common sample: material partner panels, 2022 onward, exact chapter matches,
    # near-complete eligibility coverage; do not generalize to all UK trade.
    material=dec[(dec.year0>=2022)&(dec.eligible0>=1e8)&(dec.eligible1>=1e8)&
        (dec.eligible_coverage0>=.99)&(dec.eligible_coverage1>=.99)].copy()
    material['opposite_rate_sign']=(material.change*material.rate<0)
    material['material_reversal']=(material.change*material.rate<0)&(material.change.abs()>=.005)&(material.rate.abs()>=.005)
    material.to_csv(out/'material_panels.csv',index=False)
    sensitivity=[]
    for cutoff in [25e6,50e6,100e6,250e6,500e6]:
        for threshold in [.001,.005,.01]:
            z=dec[(dec.year0>=2022)&(dec.eligible0>=cutoff)&(dec.eligible1>=cutoff)&
                (dec.eligible_coverage0>=.99)&(dec.eligible_coverage1>=.99)]
            rev=(z.change*z.rate<0)&(z.change.abs()>=threshold)&(z.rate.abs()>=threshold)
            sensitivity.append(dict(cutoff_million=cutoff/1e6,threshold_pp=threshold*100,
                panels=len(z),reversals=int(rev.sum())))
    pd.DataFrame(sensitivity).to_csv(out/'panel_sensitivity.csv',index=False)
    # No cell is removed for a large estimated outcome; leave-one-chapter-out is
    # applied to every agricultural chapter with baseline eligibility.
    loo=[]
    for h in sorted(ch[(ch.year==2023)&(ch.eligible>0)&(pd.to_numeric(ch.hs2)<=24)].hs2):
        r=paired(x,'CH','exports',2023,2024,[c for c in agri if c!=h])
        loo.append(dict(omitted=h,**r))
    pd.DataFrame(loo).to_csv(out/'agri_leave_one_out.csv',index=False)
    weighting=[]
    z=ch[ch.hs2.isin(agri)]
    z=z[z.year==2023].merge(z[z.year==2024],on='hs2',suffixes=('0','1'))
    k=z[(z.eligible0>0)&(z.eligible1>0)]
    delta=k.used1/k.eligible1-k.used0/k.eligible0
    for method,w in [('2023 weights',k.eligible0/k.eligible0.sum()),
        ('2024 weights',k.eligible1/k.eligible1.sum()),('Equal chapter weights',np.ones(len(k))/len(k))]:
        weighting.append(dict(method=method,rate_change=float(w@delta)))
    pd.DataFrame(weighting).to_csv(out/'agri_weight_sensitivity.csv',index=False)
    section_dec=[]
    for yr in [2022,2023]:
        for direction in ['exports','imports']:
            for iso in ['CH','PL','CA']:
                z=x[(x.iso==iso)&(x.direction==direction)&x.year.isin([yr,yr+1])]
                g=z.groupby(['year','section'])[['eligible','used']].sum().reset_index()
                z0=g[g.year==yr].merge(g[g.year==yr+1],on='section',suffixes=('0','1'))
                try:r=decompose(z0.eligible0,z0.used0,z0.eligible1,z0.used1)
                except ValueError:continue
                section_dec.append(dict(iso=iso,direction=direction,year0=yr,**r))
    pd.DataFrame(section_dec).to_csv(out/'section_sensitivity.csv',index=False)
    summary=dict(rows=len(x),source_rows=sum(a['source_rows'] for a in audit),
        quarantined_year_mismatches=sum(a['quarantined_year_mismatches'] for a in audit),
        audit=audit,material_panels=len(material),
        sign_reversals=int(material.opposite_rate_sign.sum()),material_reversals=int(material.material_reversal.sum()),
        max_accounting_error=float(dec.residual.abs().max()),
        swiss=aggregate[(aggregate.iso=='CH')&(aggregate.direction=='exports')].to_dict('records'),
        bounds=bounds,swiss_agri=sr)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:summary[k] for k in ['rows','material_panels','sign_reversals','material_reversals','max_accounting_error','swiss_agri','bounds']},indent=2))

if __name__=='__main__':main()
