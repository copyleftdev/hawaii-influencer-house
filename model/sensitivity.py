"""What breaks it first, what the null hypothesis is, and what would have to be true."""
from dataclasses import replace
from fractions import Fraction as F
import calc
from calc import money, pct
from model import *
from dcf import schedule
from breakeven import fixed_costs

def irr_of(site, ops, mode, **kw):
    _, _, flows, _ = schedule(site, ops, mode, **kw)
    return calc.irr(flows)

def y3(site, ops, mode, **kw):
    _, rows, _, _ = schedule(site, ops, mode, **kw)
    return rows[2][7]

# ---------------------------------------------------------------- null hypothesis
def plain_landlord(site, ops):
    """Just buy it and rent it long-term. The bar the whole venture must clear."""
    rent = site.lease_monthly*12
    vac  = rent*F(5,100)
    eff  = rent - vac
    c = {"GET": eff*GET, "Property tax": site.proptax_resid, "Insurance": site.insurance,
         "Maintenance": site.price*site.maintenance_pct, "Management @8%": eff*F(8,100)}
    noi = eff - sum(c.values(), F(0))
    debt = calc.amortize(site.price*ops.ltv, ops.rate, ops.term_months, 12)*12
    eq = site.price*(1-ops.ltv)
    print(f"  {site.name:<26} rent {money(rent):>10}  NOI {money(noi):>9}  "
          f"debt {money(debt):>9}  net {money(noi-debt):>10}  DSCR {float(noi/debt):.2f}  "
          f"CoC {pct((noi-debt)/eq)}")

# ---------------------------------------------------------------- tornado
DRIVERS = [
    ("Brand activations sold",  lambda o,k: replace(o, activations=max(0,int(round(8*k))))),
    ("Activation fee",          lambda o,k: replace(o, activation_fee=F(55_000)*F(k))),
    ("Residency rate $/seat-mo",lambda o,k: replace(o, resid_rate=F(6_500)*F(k))),
    ("Residency occupancy",     lambda o,k: replace(o, resid_occ=min(F(1), F(70,100)*F(k)))),
    ("Retreat price",           lambda o,k: replace(o, retreat_price=F(7_500)*F(k))),
    ("Production day rate",     lambda o,k: replace(o, prod_day_rate=F(4_500)*F(k))),
    ("Staff cost",              lambda o,k: replace(o, staff_loaded=F(265_000)*F(k))),
    ("Mortgage rate",           lambda o,k: replace(o, rate=F("7.25")/100*F(k))),
    ("Appreciation",            lambda o,k: replace(o, appreciation=F(3,100)*F(k))),
    ("Build-out capex",         lambda o,k: replace(o, capex=F(610_000)*F(k))),
]

def tornado(site, mode, lo=F(75,100), hi=F(125,100)):
    base_ops = Ops()
    b = irr_of(site, base_ops, mode)
    rows = []
    for name, fn in DRIVERS:
        try:
            a = irr_of(site, fn(base_ops, lo), mode)
            c = irr_of(site, fn(base_ops, hi), mode)
        except ValueError:
            continue
        rows.append((name, a, c, abs(c-a)))
    rows.sort(key=lambda r: -r[3])
    print(f"\n  base 10-yr IRR {b*100:.2f}%   (each driver moved -25% / +25%)")
    print(f"  {'driver':<28}{'-25%':>10}{'+25%':>10}{'swing':>10}")
    for n,a,c,s in rows:
        bar = "#"*max(1,int(s*100*1.2))
        print(f"  {n:<28}{a*100:>9.2f}%{c*100:>9.2f}%{s*100:>9.2f}pp  {bar}")

# ---------------------------------------------------------------- what would have to be true
def required(site, mode, target=F(15,100), field="activation_fee", base=F(55_000)):
    lo, hi = F(1,10), F(20)
    for _ in range(40):
        mid = (lo+hi)/2
        ops = replace(Ops(), **{field: base*mid})
        try:
            r = irr_of(site, ops, mode)
        except ValueError:
            hi = mid; continue
        if r < float(target): lo = mid
        else: hi = mid
    return base*(lo+hi)/2

if __name__ == "__main__":
    ops = Ops()
    print("="*80)
    print("NULL HYPOTHESIS — skip the business, just be a landlord")
    print("="*80)
    for s in (OAHU, KONA): plain_landlord(s, ops)
    print("\n  => No Hawaii house at these prices cash-flows as a plain rental. The operating")
    print("     business is the only thing that can carry the asset. The question is whether")
    print("     it carries it far enough to be worth doing.")

    print("\n" + "="*80); print("TORNADO — Hawaii Island, BUY"); print("="*80)
    tornado(KONA, "buy")
    print("\n" + "="*80); print("TORNADO — Oahu, BUY"); print("="*80)
    tornado(OAHU, "buy")

    print("\n" + "="*80)
    print("WHAT WOULD HAVE TO BE TRUE for a 15% 10-year IRR")
    print("="*80)
    for site, mode in ((KONA,"buy"), (KONA,"lease"), (OAHU,"buy")):
        f = required(site, mode, F(15,100), "activation_fee", F(55_000))
        r = required(site, mode, F(15,100), "resid_rate", F(6_500))
        print(f"  {site.name} — {mode}")
        print(f"     brand activation fee must reach {money(f)} per 5-day takeover "
              f"({float(f/55_000):.1f}x plan), 8 per year")
        print(f"     OR residency must price at {money(r)}/seat-month "
              f"({float(r/6_500):.1f}x plan) = {money(r*12)}/creator/yr")
