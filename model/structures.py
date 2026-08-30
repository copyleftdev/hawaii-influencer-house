"""The three structural trades that actually move the number."""
from dataclasses import replace
from fractions import Fraction as F
import calc
from calc import money, pct
from model import *
from dcf import schedule, LAND, COSTSEG, CAPEX_5YR, TAX_ORD

def irr_npv(site, ops, mode, **kw):
    _,_,flows,_ = schedule(site, ops, mode, **kw)
    return calc.irr(flows), calc.npv(F(12,100), flows), flows

print("="*86)
print("TRADE 1 — Lease term length. The 180-day line moves TAT *and* passive-loss status.")
print("="*86)
print("""
  180+ consecutive days to one tenant  -> TAT does not apply (GET only), and Oahu's
     30-day minimum is comfortably cleared. BUT it is unambiguously a *rental activity*
     under Reg 1.469-1T(e)(3), so losses are passive and the year-1 bonus depreciation
     is trapped until you have passive income or you sell.

  30-179 days WITH significant personal services (production support, programming,
     housekeeping, meals) -> NOT a rental activity under the 1.469-1T(e)(3)(ii)(B)
     exception, so material participation makes it non-passive and the year-1
     depreciation offsets other income. COST: 14% TAT on the lodging line.
""")
ops = Ops()
for site, mode in ((KONA,"buy"), (OAHU,"buy"), (KONA,"lease")):
    a = irr_npv(site, replace(ops, term_180_plus=True),  mode, shield_usable=False)
    b = irr_npv(site, replace(ops, term_180_plus=False), mode, shield_usable=True)
    base = run(site, ops, mode)
    tat = base.rev["Creator residencies"]*TAT
    bldg = site.price*(1-LAND[site.county]) if mode=="buy" else F(0)
    bonus = bldg*COSTSEG + ops.capex*CAPEX_5YR
    print(f"  {site.name} — {mode}")
    print(f"    A) 180+ day terms, losses suspended    IRR {a[0]*100:>6.2f}%   NPV@12% {money(a[1]):>12}")
    print(f"    B) 30-day terms + services, shield on  IRR {b[0]*100:>6.2f}%   NPV@12% {money(b[1]):>12}")
    print(f"       annual TAT cost of choosing B: {money(tat)}   "
          f"year-1 bonus depreciation unlocked: {money(bonus)} "
          f"(~{money(bonus*TAX_ORD)} of tax)")
    print(f"       -> {'B wins' if b[1] > a[1] else 'A wins'} by {money(abs(b[1]-a[1]))} of NPV\n")

print("="*86)
print("TRADE 2 — GET pyramiding in a PropCo/OpCo structure, and the 237-16.5 fix")
print("="*86)
rent = OAHU.lease_monthly*12
naive = rent*GET
ded   = rent*F(875,1000)
fixed = (rent-ded)*GET
print(f"  PropCo charges OpCo {money(rent)}/yr of rent for the house.")
print(f"    GET on that rent, no planning ............ {money(naive)}/yr  (pure pyramiding)")
print(f"    HRS 237-16.5 sublease deduction @87.5% ... {money(fixed)}/yr")
print(f"    saved .................................... {money(naive-fixed)}/yr")
print("""
  Conditions: the sublease must be of the SAME real property, in WRITING, and the
  lessor (PropCo) must give OpCo a certificate that it is GET-licensed and taxable.
  The deduction covers the room/space sublease line only - service revenue
  (production support, activations, retreats) gets no deduction and pays full GET.
  File Form G-72 with the return.
""")

print("="*86)
print("TRADE 3 — Opportunity Zone. Kailua-Kona has two designated tracts.")
print("="*86)
_,_,_,ex = schedule(KONA, ops, "buy")
tax_at_exit = ex["t1245"] + ex["t1250"] + ex["tcap"]
print(f"  Kona BUY, 10-year hold, taxes owed at exit:")
print(f"    section 1245 recapture on cost-seg'd property ... {money(ex['t1245'])}")
print(f"    section 1250 unrecaptured depreciation .......... {money(ex['t1250'])}")
print(f"    long-term capital gain ......................... {money(ex['tcap'])}")
print(f"    TOTAL .......................................... {money(tax_at_exit)}")
print(f"\n  Inside a Qualified Opportunity Fund held 10+ years the basis steps up to FMV,")
print(f"  which eliminates essentially all of that: ~{money(tax_at_exit)} of value,")
print(f"  or {pct(tax_at_exit/(site.price*(1-ops.ltv)+ops.capex),1)} of the equity going in.")
flows_std = schedule(KONA, ops, "buy")[2]
flows_oz  = list(flows_std); flows_oz[-1] = calc.cents(flows_oz[-1] + tax_at_exit)
print(f"\n    standard structure   IRR {calc.irr(flows_std)*100:>6.2f}%   NPV@12% {money(calc.npv(F(12,100),flows_std))}")
print(f"    inside a QOF         IRR {calc.irr(flows_oz)*100:>6.2f}%   NPV@12% {money(calc.npv(F(12,100),flows_oz))}")
print("""
  The catch: a QOF must SUBSTANTIALLY IMPROVE the property - double the basis of the
  building (excluding land) within 30 months. A $610k build-out on a ~$1.8M building
  does NOT clear it. To use the OZ you must buy a tired, cheap building inside the
  tract and spend more on the conversion than you paid for the structure. That
  happens to be what a production house wants anyway.
  Note also: you must be rolling in ELIGIBLE CAPITAL GAINS, not ordinary savings.
""")
