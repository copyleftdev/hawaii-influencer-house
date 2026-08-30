from dataclasses import replace
from fractions import Fraction as F
import calc
from calc import money, pct
from model import *
from dcf import schedule

WIN = dict(term_180_plus=False, prod_day_rate=F(6_618), prod_days=45,
           activation_fee=F(72_000), activations=10)

def go(ops, site=KONA, mode="buy"):
    b = run(site, ops, mode)
    _,_,fl,_ = schedule(site, ops, mode, shield_usable=True)
    return b, calc.irr(fl), calc.npv(F(12,100), fl)

print("="*92)
print("FRAGILITY OF THE WINNING CASE — everything rests on brand activations")
print("="*92)
print(f"{'activations/yr':>15}{'act. revenue':>15}{'total rev':>13}{'NOI':>11}{'DSCR':>7}{'IRR':>9}{'NPV@12%':>13}")
for n in (2,4,6,8,10,12):
    b,irr,npv = go(replace(Ops(), **{**WIN, "activations": n}))
    print(f"{n:>15}{money(F(n)*F(72_000)):>15}{money(b.gross):>13}{money(b.noi):>11}"
          f"{float(b.dscr):>7.2f}{irr*100:>8.2f}%{money(npv):>13}")
print("\n  Scenario 4 needs ~8 sold takeovers a year to hold a 12% return, and ~5 to avoid")
print("  losing money. Below 4 the whole thing is underwater regardless of everything else.")

print("\n" + "="*92)
print("WHY THE OPPORTUNITY ZONE LOST: capex is unlevered, purchase price is not")
print("="*92)
ops70 = replace(Ops(), **WIN)
print(f"  Kona standard:  0.30 x $2,600,000 + $610,000 capex   = {money(F(2_600_000)*F(30,100)+F(610_000))} equity")
print(f"  Kona OZ shell:  0.30 x $1,900,000 + $1,400,000 capex = {money(F(1_900_000)*F(30,100)+F(1_400_000))} equity")
print(f"  The OZ step-up was worth $248,017. The extra equity required was "
      f"{money(F(1_900_000)*F(30,100)+F(1_400_000) - (F(2_600_000)*F(30,100)+F(610_000)))}.")
print("  The subsidy does not cover the capital it forces you to commit unlevered.")
print("  => an OZ play only works if the renovation is DEBT-FINANCED (construction loan),")
print("     which restores the leverage the substantial-improvement test destroys.")

print("\n" + "="*92)
print("IS A $72,000 FIVE-DAY BRAND TAKEOVER A REAL PRICE?")
print("="*92)
creators, posts, rate = 6, 3, F(5_000)
content_value = F(creators*posts)*rate
print(f"  6 resident creators x 3 posts each at the low end of the mid-tier rate card ($5,000)")
print(f"    = {creators*posts} pieces of creator content worth {money(content_value)} bought a la carte")
print(f"  plus a produced hero film, stills, and a location the brand cannot buy on Oahu")
print(f"  => {money(F(72_000))} is BELOW the a-la-carte cost of the same content. The price holds.")
print(f"  The risk is not price. It is whether 8-10 brands per year will book Hawaii at all.")
