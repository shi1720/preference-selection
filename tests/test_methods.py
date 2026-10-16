"""Independent exhaustive arithmetic and numerical-programming checks."""
from pathlib import Path
import sys, unittest
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from scipy.optimize import linprog
from methods import retention_bounds,fixed_retention_bounds,decompose

class MethodsTest(unittest.TestCase):
    def test_bounds_exhaustive_rational(self):
        count=0
        for e in range(1,9):
            for p in range(e+1):
                for a in range(9):
                    for q in range(a+1):
                        values=[F(p+v,e+v+w) for v in range(q+1) for w in range(a-q+1)]
                        lo,hi=retention_bounds(e,p,a,q)
                        self.assertAlmostEqual(lo,float(min(values)),places=14)
                        self.assertAlmostEqual(hi,float(max(values)),places=14)
                        for r in range(a+1):
                            exact=[F(p+v,e+r) for v in range(q+1) if 0<=r-v<=a-q]
                            l,u=fixed_retention_bounds(e,p,a,q,r)
                            self.assertAlmostEqual(l,float(min(exact)),places=14)
                            self.assertAlmostEqual(u,float(max(exact)),places=14)
                        count+=1
        self.assertEqual(count,1980)

    def test_charnes_cooper_lp(self):
        rng=np.random.default_rng(1720406)
        for _ in range(200):
            e=float(rng.uniform(1,100));p=e*rng.random();a=float(rng.uniform(0,100));q=a*rng.random()
            # variables x = retained used * t, y = retained unused * t, t.
            c=np.array([1.,0.,p]);A=[[1,0,-q],[0,1,-(a-q)]]
            kwargs=dict(A_ub=A,b_ub=[0,0],A_eq=[[1,1,e]],b_eq=[1],bounds=(0,None),method='highs')
            low=linprog(c,**kwargs);high=linprog(-c,**kwargs)
            self.assertTrue(low.success and high.success)
            lo,hi=retention_bounds(e,p,a,q)
            self.assertAlmostEqual(lo,low.fun,places=9);self.assertAlmostEqual(hi,-high.fun,places=9)

    def test_decomposition_exact_fraction_identity(self):
        rng=np.random.default_rng(20406)
        for _ in range(1000):
            e0=rng.integers(0,20,8);e1=rng.integers(0,20,8)
            e0[0]=e1[0]=10
            p0=np.array([rng.integers(0,e+1) for e in e0]);p1=np.array([rng.integers(0,e+1) for e in e1])
            result=decompose(e0,p0,e1,p1)
            k=[i for i in range(8) if e0[i] and e1[i]]
            a0=sum(int(e0[i]) for i in k);a1=sum(int(e1[i]) for i in k)
            u0=F(sum(int(p0[i]) for i in k),a0);u1=F(sum(int(p1[i]) for i in k),a1)
            rate=F(0);weight=F(0)
            for i in k:
                w0=F(int(e0[i]),a0);w1=F(int(e1[i]),a1)
                r0=F(int(p0[i]),int(e0[i]));r1=F(int(p1[i]),int(e1[i]))
                rate+=(w0+w1)*(r1-r0)/2;weight+=(r0+r1)*(w1-w0)/2
            exit_term=sum((F(int(e0[i]))*u0-int(p0[i]) for i in range(8) if e0[i] and not e1[i]),F(0))/int(e0.sum())
            entry_term=sum((F(int(p1[i]))-int(e1[i])*u1 for i in range(8) if e1[i] and not e0[i]),F(0))/int(e1.sum())
            total=F(int(p1.sum()),int(e1.sum()))-F(int(p0.sum()),int(e0.sum()))
            self.assertEqual(total,rate+weight+exit_term+entry_term)
            for name,val in [('rate',rate),('weight',weight),('exit',exit_term),('entry',entry_term)]:
                self.assertAlmostEqual(result[name],float(val),places=13)

    def test_zero_and_missing_rejected(self):
        with self.assertRaises(ValueError):decompose([0],[0],[0],[0])
        with self.assertRaises(ValueError):decompose([1],[np.nan],[1],[1])
        with self.assertRaises(ValueError):decompose([1],[2],[1],[1])
        with self.assertRaises(ValueError):retention_bounds(0,0,1,0)

if __name__=='__main__':unittest.main(verbosity=2)
