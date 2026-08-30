"""Same paths, two exit routes.

Reports NPV as primary. IRR is undefined whenever the cash flows never change
sign - which happens on precisely the worst paths - so ranking by IRR silently
deletes the bad outcomes and flatters the distribution. NPV always exists.
"""
import random
from dataclasses import replace
from fractions import Fraction as F
import calc
from calc import money, pct
from model import *
from dcf import schedule, INFLATE
from pro import WIN, correlated

site, mode = KONA, "buy"
HURDLE = F(12,100)

def path(ops, cap=None):
    b = run(site, ops, mode)
    _,_,fl,ex = schedule(site, ops, mode, shield_usable=True)
    if cap is not None:
        # A rational seller takes the BETTER of the two exits. The residential value
        # is a floor under the operating business - effectively a free put, and the
        # strongest argument for owning rather than leasing.
        biz_val = max(F(0), b.noi)*(1+INFLATE)**ops.hold_years/F(cap,100)
        val = max(biz_val, ex["value"])
        new = val*(1-ops.sale_costs) - ex["balance"]
        new -= max(F(0), val*(1-ops.sale_costs) - ex["basis"])*F(28,100)
        fl = list(fl); fl[-1] = calc.cents(fl[-1] - ex["proceeds"] + new)
    return calc.npv(HURDLE, fl), calc.irr(fl), (float(b.dscr) if b.dscr else 0)

def tri(lo, m, hi, r):
    u = r.random(); c = (m-lo)/(hi-lo)
    return lo + (u*(hi-lo)*(m-lo))**0.5 if u < c else hi - ((1-u)*(hi-lo)*(hi-m))**0.5

r = random.Random(20260829); N = 600
H = {"npv": [], "irr": []}; B = {"npv": [], "irr": []}; dscrs = []
for _ in range(N):
    d = tri(0.45, 0.85, 1.25, r); cost = tri(0.95, 1.05, 1.30, r)
    o = replace(Ops(), **correlated(f"{d:.4f}"),
                staff_loaded=F(265_000)*F(f"{cost:.4f}"), capex=F(610_000)*F(f"{cost:.4f}"))
    for tag, cap in (("H", None), ("B", 10)):
        npv, irr, ds = path(o, cap)
        (H if tag=="H" else B)["npv"].append(float(npv))
        if irr is not None: (H if tag=="H" else B)["irr"].append(float(irr))
        if tag=="H": dscrs.append(ds)

def q(v, p): return calc._run("stats", {"intent":"percentile","values":sorted(v),"p":p})["value"]

def summarize(name, d):
    npv, irr = d["npv"], d["irr"]
    print(f"\n  {name}")
    print("    NPV@12%  " + "  ".join(f"P{p}:{money(F(round(q(npv,p)))):>12}" for p in (10,25,50,75,90)))
    print(f"    P(NPV > 0) .................... {pct(F(sum(1 for x in npv if x>0),len(npv)),1)}")
    print(f"    P(NPV < -$500k, badly hurt) ... {pct(F(sum(1 for x in npv if x<-500_000),len(npv)),1)}")
    print(f"    IRR (defined on {len(irr)}/{N} paths)  " +
          "  ".join(f"P{p}:{q(irr,p)*100:>7.2f}%" for p in (25,50,75)))

print("="*90)
print(f"{N} correlated paths — demand triangular(0.45, 0.85, 1.25), cost (0.95, 1.05, 1.30)")
print("  Base plan sits at demand = 1.0, which is the 82nd percentile of this distribution.")
print("="*90)
summarize("EXIT AS A HOUSE (3%/yr appreciation) — what the first model assumed", H)
summarize("EXIT AT max(HOUSE, BUSINESS @10% cap) — the house is a floor", B)
print(f"\n  P(DSCR < 1.0 in the stabilized year) ... {pct(F(sum(1 for d in dscrs if 0<d<1),len(dscrs)),1)}")
print(f"""
  Note what IRR did: it is undefined on {N-len(H['irr'])} of {N} house paths and
  {N-len(B['irr'])} of {N} business paths, because those flows never change sign.
  Those are the WORST paths. Ranking on IRR deletes them and reports a healthier
  business than exists. Every probability above is computed on NPV for that reason.""")
