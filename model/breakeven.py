"""Breakeven analysis. Affine equations solved exactly by agent-calc."""
from fractions import Fraction as F
import calc
from calc import E, sym, add, sub, mul, div, money, pct
from model import *

NIGHTS_PER_SEAT_MONTH = F(365,12)

def fixed_costs(site, ops, mode, proptax="resid"):
    """Everything that does not scale with a seat sold."""
    c = {}
    if mode == "buy":
        c["debt"] = calc.amortize(site.price*ops.ltv, ops.rate, ops.term_months, 12)*12
        c["proptax"] = site.proptax_resid if proptax=="resid" else site.proptax_hotel
        c["insurance"] = site.insurance
        c["maint"] = site.price*site.maintenance_pct
    else:
        c["lease"] = site.lease_monthly*12
        c["insurance"] = site.insurance/2
        c["maint"] = site.price*site.maintenance_pct/3
    c["utilities"] = site.utilities
    c["staff"] = ops.staff_loaded
    c["founder"] = ops.founder_comp
    c["marketing"] = ops.marketing
    c["legal"] = ops.legal_accounting
    c["software"] = ops.software_gear
    return sum(c.values(), F(0)), c

def residency_only_breakeven(site, ops, mode, proptax="resid"):
    """Seat-months of residency needed to cover everything, residency as the ONLY engine.
       fixed = S * [ rate*(1 - GET - fees - TAT?) - nights*consumables ]"""
    fx, _ = fixed_costs(site, ops, mode, proptax)
    tat = F(0) if ops.term_180_plus else TAT
    contrib = ops.resid_rate*(1 - GET - ops.payment_fees - tat) - NIGHTS_PER_SEAT_MONTH*ops.consumables_bednight
    r = calc.solve_linear(mul(E(contrib), sym("S")), E(fx), "S")
    S = F(int(r["solutions"][0]["numerator"]), int(r["solutions"][0]["denominator"]))
    return S, contrib, fx

def residency_only_rate(site, ops, mode, seat_months, proptax="resid"):
    """Price per seat-month needed to break even on residency alone at a given occupancy."""
    fx, _ = fixed_costs(site, ops, mode, proptax)
    tat = F(0) if ops.term_180_plus else TAT
    k = seat_months*(1 - GET - ops.payment_fees - tat)
    consum = seat_months*NIGHTS_PER_SEAT_MONTH*ops.consumables_bednight
    r = calc.solve_linear(sub(mul(E(k), sym("R")), E(consum)), E(fx), "R")
    return F(int(r["solutions"][0]["numerator"]), int(r["solutions"][0]["denominator"]))

def mix_breakeven_utilization(site, ops, mode, proptax="resid"):
    """Scale the whole base-case revenue mix by x; solve for x where net cash flow = 0."""
    base = run(site, ops, mode, proptax)
    variable = (base.gross*(GET+ops.payment_fees)
                + sum((v[1] for v in base.eng.values()), F(0))
                + base.used*ops.consumables_bednight)
    fx, _ = fixed_costs(site, ops, mode, proptax)
    contrib = base.gross - variable
    r = calc.solve_linear(mul(E(contrib), sym("x")), E(fx), "x")
    x = F(int(r["solutions"][0]["numerator"]), int(r["solutions"][0]["denominator"]))
    return x, base, contrib, fx

def report():
    ops = Ops()
    print("="*80)
    print("Q1.  Can creator RENT alone carry the house?  (residency is the only engine)")
    print("="*80)
    cap_seat_months = F(ops.beds*12)
    for site in (OAHU, KONA):
        for mode in ("buy","lease"):
            S, contrib, fx = residency_only_breakeven(site, ops, mode)
            need_occ = S/cap_seat_months
            print(f"\n  {site.name} — {mode}")
            print(f"    fixed cost to cover           {money(fx):>12}")
            print(f"    contribution / seat-month     {money(contrib):>12}   (at ${int(ops.resid_rate):,}/mo, 180+ day terms)")
            print(f"    seat-months needed            {float(S):>12.1f}   of {int(cap_seat_months)} the house has")
            print(f"    implied occupancy             {pct(need_occ,1):>12}", end="")
            print("   <-- IMPOSSIBLE" if need_occ > 1 else "   feasible")
            if need_occ <= 1:
                print(f"    creators/yr @ 6-mo terms      {float(S/6):>12.1f}")
                print(f"    creators/yr @ 3-mo terms      {float(S/3):>12.1f}")
    print()
    print("="*80)
    print("Q2.  What rent WOULD carry it, at a realistic 75% residency occupancy?")
    print("="*80)
    for site in (OAHU, KONA):
        for mode in ("buy","lease"):
            R = residency_only_rate(site, ops, mode, cap_seat_months*F(75,100))
            print(f"  {site.name:<26} {mode:<6}  {money(R):>10}/seat-month   "
                  f"= {money(R*12)}/creator/yr")
    print()
    print("="*80)
    print("Q3.  With the full four-engine mix, how much of plan must you actually hit?")
    print("="*80)
    for site in (OAHU, KONA):
        for mode in ("buy","lease"):
            x, base, contrib, fx = mix_breakeven_utilization(site, ops, mode)
            print(f"\n  {site.name} — {mode}")
            print(f"    contribution at 100% of plan  {money(contrib):>12}")
            print(f"    fixed cost                    {money(fx):>12}")
            print(f"    breakeven = {pct(x,1)} of plan   (plan gross {money(base.gross)}"
                  f" -> breakeven gross {money(base.gross*x)})")
            print(f"    margin of safety              {pct(1-x,1):>12}")

if __name__ == "__main__":
    report()
