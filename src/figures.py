"""Publication figures; no downloaded or generated illustrative images."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';F=ROOT/'figures'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
    'axes.spines.right':False,'axes.labelsize':10,'legend.frameon':False,
    'savefig.bbox':'tight','pdf.fonttype':42,'ps.fonttype':42})
BLUE='#244a73';TEAL='#267f7f';ORANGE='#bd6c26';GRAY='#727b86'

def save(fig,name):
    fig.savefig(F/f'{name}.pdf');fig.savefig(F/f'{name}.png',dpi=220);plt.close(fig)

def main():
    groups=pd.read_csv(R/'swiss_groups.csv')
    fig,ax=plt.subplots(figsize=(6.7,3.6))
    for group,label,color,marker in [('All chapters','All eligible chapters',BLUE,'o'),
        ('Agriculture 01-24','Agriculture (01-24)',TEAL,'s'),
        ('Certain exit 25-97 excl 35,38','Industrial chapters without mixed exceptions',ORANGE,'^')]:
        z=groups[groups.group==group]
        ax.plot(z.year,z.pur*100,label=label,color=color,marker=marker,lw=1.8)
    ax.axvline(2024,color=GRAY,ls=':',lw=1);ax.set(xlabel='Year',ylabel='Preference utilization (%)',ylim=(25,78),xticks=[2021,2022,2023,2024])
    ax.legend(loc='lower right',fontsize=8);ax.grid(axis='y',alpha=.16)
    save(fig,'01_swiss_rates')

    fig,axes=plt.subplots(1,2,figsize=(7,3.7),sharey=True)
    names=['Agriculture 01-24','Mixed chapters 35,38','Certain exit 25-97 excl 35,38']
    labels=['01-24','35, 38','Other 25-97']
    for ax,year in zip(axes,[2023,2024]):
        z=groups[groups.year==year].set_index('group').loc[names]
        ax.bar(labels,z.used/1e6,color=TEAL,label='Used preference')
        ax.bar(labels,z.unused/1e6,bottom=z.used/1e6,color=ORANGE,label='Eligible, unused')
        ax.set_title(str(year));ax.tick_params(axis='x',labelsize=8);ax.grid(axis='y',alpha=.15)
    axes[0].set_ylabel('Preference-eligible exports (GBP million)')
    axes[1].legend(loc='upper right',fontsize=8)
    fig.tight_layout();save(fig,'02_eligible_mass')

    b=pd.read_csv(R/'swiss_retention_bounds.csv')
    fig,ax=plt.subplots(figsize=(6.7,3.4))
    for i,z in b.iterrows():
        ax.plot([z.lower*100,z.upper*100],[i,i],color=BLUE,lw=5,solid_capstyle='butt')
        ax.plot(z.base_pur*100,i,'o',color=GRAY,label='Observed base-year rate' if i==0 else None)
        ax.plot(z.certain_exit_only*100,i,'s',color=ORANGE,label='Remove certain-exit chapters only' if i==0 else None)
    ax.axvline(b.observed_2024.iloc[0]*100,color=TEAL,ls='--',label='Observed 2024 rate')
    ax.set(yticks=range(3),yticklabels=b.base_year.astype(str),xlabel='Preference utilization (%)',ylabel='Frozen-basket base year',xlim=(30,80),ylim=(-.5,3.0))
    ax.legend(loc='upper left',fontsize=8,ncol=1);ax.grid(axis='x',alpha=.15)
    save(fig,'03_retention_bounds')

    dec=pd.read_csv(R/'decompositions.csv');z=dec[(dec.iso=='CH')&(dec.direction=='exports')&(dec.year0==2023)].iloc[0]
    fig,ax=plt.subplots(figsize=(6.7,3.4));base=0
    for i,key in enumerate(['rate','weight','exit','entry']):
        v=z[key]*100;ax.bar(i,v,bottom=base,color=ORANGE if v<0 else BLUE,width=.65)
        ax.text(i,base+v+(.7 if v>=0 else -1.5),f'{v:+.2f}',ha='center',fontsize=9)
        base+=v
        ax.plot([i+.325,i+.675],[base,base],color=GRAY,lw=.7)
    ax.bar(4,z.change*100,color=TEAL,width=.65);ax.text(4,z.change*100+.7,f'{z.change*100:+.2f}',ha='center')
    ax.axhline(0,color=GRAY,lw=.7);ax.set(xticks=range(5),xticklabels=['Within-chapter\nrates','Chapter\nweights','Eligibility\nexit','Eligibility\nentry','Total'],ylabel='Contribution (percentage points)',ylim=(-9,22))
    ax.grid(axis='y',alpha=.15);save(fig,'04_decomposition')

    x=pd.read_csv(R/'material_panels.csv');fig,axes=plt.subplots(1,2,figsize=(7.2,3.5))
    rev=x.material_reversal
    for ax in axes:
        ax.scatter(x.loc[~rev,'change']*100,x.loc[~rev,'rate']*100,s=17,color=GRAY,alpha=.55,label='Other panels')
        ax.scatter(x.loc[rev,'change']*100,x.loc[rev,'rate']*100,s=25,color=ORANGE,label='Material sign reversal')
        ax.axhline(0,color=GRAY,lw=.8);ax.axvline(0,color=GRAY,lw=.8);ax.grid(alpha=.12)
        ax.set_xlabel('Observed change (pp)')
    for iso,y0,offset in [('CH',2023,(-72,-27)),('PL',2022,(0,22)),('CA',2023,(-4,36))]:
        q=x[(x.iso==iso)&(x.year0==y0)&(x.direction=='exports')].iloc[0]
        axes[1].annotate(f'{iso} exports\n{y0}-{str(y0+1)[-2:]}',(q.change*100,q.rate*100),xytext=offset,textcoords='offset points',fontsize=7,arrowprops=dict(arrowstyle='-',color=GRAY,lw=.7))
    axes[0].set_ylabel('Within-chapter rate component (pp)');axes[0].set_title('All 184 panels',fontsize=10)
    axes[1].set(xlim=(-16,21),ylim=(-9,10),title='Detail')
    axes[0].legend(loc='lower right',fontsize=7);fig.tight_layout();save(fig,'05_panel_reversals')

    c=pd.read_csv(R/'swiss_retention_curve.csv');fig,ax=plt.subplots(figsize=(6.7,3.4))
    ax.fill_between(c.retained_million,c.lower*100,c.upper*100,color=BLUE,alpha=.2,label='Feasible selection interval')
    ax.plot(c.retained_million,c.lower*100,color=BLUE);ax.plot(c.retained_million,c.upper*100,color=BLUE)
    ax.axhline(b.observed_2024.iloc[0]*100,color=TEAL,ls='--',label='Observed 2024 rate')
    ax.set(xlabel='2023 eligible value retained in chapters 35 and 38 (GBP million)',ylabel='Frozen-basket utilization (%)')
    ax.legend(fontsize=8,loc='upper right');ax.grid(alpha=.12);save(fig,'06_fixed_retention')

if __name__=='__main__':main()
