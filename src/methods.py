"""Accounting methods. Inputs are values, not pre-rounded published percentages."""
import numpy as np

def ratio(p,e):
    if e<=0: raise ValueError('A positive denominator is required')
    return p/e

def decompose(e0,p0,e1,p1):
    """Four-term decomposition on an explicitly matched, fully observed cell universe.

    Entry/exit are changes in positive aggregate eligibility, not proof of policy changes.
    Common-support rates use weights normalized within common support. The symmetric
    rate/weight split is the classical Kitagawa identity.
    """
    e0,p0,e1,p1=[np.asarray(x,dtype=float) for x in [e0,p0,e1,p1]]
    if not all(np.all(np.isfinite(x)) for x in [e0,p0,e1,p1]):
        raise ValueError('Missing values must be handled explicitly')
    if any(np.any(x < -1e-8) for x in [e0,p0,e1,p1]) or np.any(p0>e0+1e-8) or np.any(p1>e1+1e-8):
        raise ValueError('Invalid eligibility or use values')
    k=(e0>0)&(e1>0); d=(e0>0)&(e1==0); n=(e0==0)&(e1>0)
    if not k.any():raise ValueError('No common eligible support')
    w0=e0[k]/e0[k].sum();w1=e1[k]/e1[k].sum()
    u0=p0[k]/e0[k];u1=p1[k]/e1[k]
    uk0=float(w0@u0);uk1=float(w1@u1)
    exit_term=(e0[d].sum()*uk0-p0[d].sum())/e0.sum()
    entry_term=(p1[n].sum()-e1[n].sum()*uk1)/e1.sum()
    rate=float(((w0+w1)/2)@(u1-u0))
    weight=float(((u0+u1)/2)@(w1-w0))
    change=p1.sum()/e1.sum()-p0.sum()/e0.sum()
    return dict(change=change,rate=rate,weight=weight,exit=exit_term,entry=entry_term,
        residual=change-rate-weight-exit_term-entry_term,
        common_rate0=uk0,common_rate1=uk1,common_cells=int(k.sum()),
        exit_cells=int(d.sum()),entry_cells=int(n.sum()),
        eligible0=float(e0.sum()),eligible1=float(e1.sum()),
        exit_eligible0=float(e0[d].sum()),entry_eligible1=float(e1[n].sum()))

def retention_bounds(e_keep,p_keep,e_amb,p_amb):
    """Sharp utilization bounds after certain removal and unrestricted partial retention.

    In the ambiguous pool, used and unused eligible value can be retained separately.
    Known-retained eligible mass must be positive. The endpoints are attained by
    retaining all ambiguous unused value only, or all ambiguous used value only.
    """
    if not (e_keep>0 and 0<=p_keep<=e_keep and 0<=p_amb<=e_amb):
        raise ValueError('Invalid retained/ambiguous pool')
    return (p_keep/(e_keep+e_amb-p_amb),(p_keep+p_amb)/(e_keep+p_amb))

def fixed_retention_bounds(e_keep,p_keep,e_amb,p_amb,r):
    if not 0<=r<=e_amb:raise ValueError('Invalid retained mass')
    return ((p_keep+max(0,r-(e_amb-p_amb)))/(e_keep+r),
            (p_keep+min(r,p_amb))/(e_keep+r))
