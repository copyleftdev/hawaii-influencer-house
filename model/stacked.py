"""Stack every lever that survived scrutiny and find the ceiling."""
from dataclasses import replace
from fractions import Fraction as F
import calc
from calc import money, pct
from model import *
from dcf import schedule, TAX_ORD
import dcf

# A tired building inside the Kailua-Kona opportunity zone, bought cheap and gutted.
# Substantial-improvement test: capex on the building must EXCEED the building basis.
KONA_OZ = Site("Hawaii Island — Kona OZ tract", "Hawaii",
               F(1_900_000), F(12_000), P("27"), P("32"),
               F(26_000), F(34_000), F("1.5")/100,
               F(1_900_000)*F("11.10")/1000, F(1_900_000)*F("11.55")/1000)

def variant(**kw):
    return replace(Ops(), **kw)

SCENARIOS = [
  ("0  Base plan, Oahu, buy",              OAHU,    "buy",  variant(), dict(shield_usable=False)),
  ("1  Move to a neighbor island",         KONA,    "buy",  variant(), dict(shield_usable=False)),
  ("2  + 30-day terms & real services",    KONA,    "buy",  variant(term_180_plus=False), dict(shield_usable=True)),
  ("3  + price location days to the 32% credit", KONA, "buy",
       variant(term_180_plus=False, prod_day_rate=F(6_618), prod_days=45), dict(shield_usable=True)),
  ("4  + brand activations at $72k x10",   KONA,    "buy",
       variant(term_180_plus=False, prod_day_rate=F(6_618), prod_days=45,
               activation_fee=F(72_000), activations=10), dict(shield_usable=True)),
  ("5  + OZ basis (cheap shell, heavy build)", KONA_OZ, "buy",
       variant(term_180_plus=False, prod_day_rate=F(6_618), prod_days=45,
               activation_fee=F(72_000), activations=10,
               capex=F(1_400_000), capex_short_life=F(55,100)), dict(shield_usable=True)),
]

print("="*100)
print(f"{'scenario':<46}{'gross rev':>12}{'NOI':>11}{'DSCR':>7}{'equity':>12}{'IRR':>8}{'NPV@12%':>13}")
print("="*100)
oz_credit = None
for label, site, mode, ops, kw in SCENARIOS:
    base = run(site, ops, mode, )
    _,_,flows,ex = schedule(site, ops, mode, **kw)
    if label.startswith("5"):
        tax_exit = ex["t1245"]+ex["t1250"]+ex["tcap"]
        flows = list(flows); flows[-1] = calc.cents(flows[-1]+tax_exit); oz_credit = tax_exit
    irr = calc.irr(flows); npv = calc.npv(F(12,100), flows)
    print(f"{label:<46}{money(base.gross):>12}{money(base.noi):>11}"
          f"{(float(base.dscr) if base.dscr else 0):>7.2f}{money(-flows[0]):>12}"
          f"{irr*100:>7.2f}%{money(npv):>13}")
print("="*100)
print(f"(scenario 5 credits {money(oz_credit)} of exit tax eliminated by the 10-year QOF step-up)")

label, site, mode, ops, kw = SCENARIOS[-1]
base = run(site, ops, mode)
_,rows,flows,ex = schedule(site, ops, mode, **kw)
print(f"\n{'='*100}\nFULLY STACKED CONFIGURATION — detail\n{'='*100}")
print(f"{'REVENUE':<30}{'gross':>13}{'bed-nights':>12}{'net $/bed-night':>18}")
for k,(g,d,bn) in sorted(base.eng.items(), key=lambda x: -((x[1][0]-x[1][1])/x[1][2] if x[1][2] else 0)):
    print(f"  {k:<28}{money(g):>13}{int(bn):>12,}{money((g-d)/bn if bn else 0):>18}")
print(f"  {'TOTAL':<28}{money(base.gross):>13}{int(base.used):>12,}   utilization {pct(base.used/base.cap,1)}")
print(f"\n  NOI {money(base.noi)}   margin {pct(base.noi/base.gross,1)}   "
      f"debt {money(base.debt)}   DSCR {float(base.dscr):.2f}   net {money(base.net)}")
print(f"\n{'yr':>3}{'revenue':>13}{'EBITDA':>12}{'tax':>12}{'net CF':>13}")
for y,rev,ebitda,dsv,dep,tx,t,cf in rows:
    print(f"{y:>3}{money(rev):>13}{money(ebitda):>12}{money(t):>12}{money(cf):>13}")
print(f"\n  equity {money(-flows[0])}  exit proceeds {money(ex['proceeds']+ex['t1245']+ex['t1250']+ex['tcap'])} (OZ, no exit tax)")
fl = list(flows); fl[-1] = calc.cents(fl[-1]+ex["t1245"]+ex["t1250"]+ex["tcap"])
print(f"  10-yr IRR {calc.irr(fl)*100:.2f}%   NPV@12% {money(calc.npv(F(12,100),fl))}   "
      f"MoIC {float(sum(fl[1:])/-fl[0]):.2f}x")
