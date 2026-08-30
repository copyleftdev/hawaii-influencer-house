"""What the first model got wrong.

Four omissions a professional modeler would flag immediately:
  1. No pre-opening period. Revenue started in month 1. It doesn't.
  2. No cash curve. "Equity in" was down-payment + capex. The real number is the
     PEAK CUMULATIVE CASH DEFICIT, which is what you actually have to fund.
  3. Exit by appreciation only. An operating asset also has a cap-rate value, and
     the two disagree - which tells you whether the business adds terminal value.
  4. One-at-a-time sensitivity. Drivers are correlated: if brands don't book,
     creators don't come either. The honest downside moves them together.
"""
from dataclasses import replace
from fractions import Fraction as F
import calc
from calc import money, pct
from model import *
from dcf import schedule, LAND, COSTSEG, TAX_ORD, INFLATE, GROWTH, RAMP
from breakeven import fixed_costs

WIN = dict(term_180_plus=False, prod_day_rate=F(6_618), prod_days=45,
           activation_fee=F(72_000), activations=10)

# Hawaii demand is seasonal: winter escape + summer. Indexed to sum to 12.
SEASON = [F(x,100) for x in (118, 112, 108, 92, 85, 105, 112, 108, 84, 82, 94, 100)]

# ---------------------------------------------------------------- pre-opening
def preopening(site, ops, mode, months=9):
    """Close, permit, renovate, hire, pre-sell. Costs run; revenue does not."""
    fx, fxd = fixed_costs(site, ops, mode)
    debt = fxd.get("debt", F(0))
    lease = fxd.get("lease", F(0))
    carry = (debt + lease
             + fxd.get("proptax", F(0)) + fxd.get("insurance", F(0))
             + site.utilities*F(40,100))/12          # utilities at 40% during build
    team  = (ops.founder_comp + ops.staff_loaded*F(35,100))/12   # founder + a manager
    presell = ops.marketing/12*F(150,100)            # pre-selling costs MORE than steady state
    legal = ops.legal_accounting/12
    monthly = carry + team + presell + legal
    return months, monthly, monthly*months

# ---------------------------------------------------------------- cash curve
def cash_curve(site, ops, mode, years=4, preopen_months=9, **kw):
    """Month-by-month cash, from the day you close. Returns (flows, cumulative)."""
    base = run(site, ops, mode)
    fx, fxd = fixed_costs(site, ops, mode)
    debt = fxd.get("debt", F(0))
    fixed_ex_debt = fx - debt
    tat_cost = F(0) if ops.term_180_plus else base.rev["Creator residencies"]*TAT
    var_rate = (base.gross*(GET+ops.payment_fees)
                + sum((v[1] for v in base.eng.values()), F(0))
                + base.used*ops.consumables_bednight + tat_cost) / base.gross

    flows = []
    # month 0: equity out the door
    n, monthly_burn, total_pre = preopening(site, ops, mode, preopen_months)
    flows.append(-(site.price*(1-ops.ltv) if mode=="buy" else F(0)) - ops.capex)
    for _ in range(n):
        flows.append(-monthly_burn)
    for y in range(1, years+1):
        g = (1+GROWTH)**(y-1)
        rev_y = base.gross*RAMP[y-1]*g
        fix_y = fixed_ex_debt*(1+INFLATE)**(y-1)
        for m in range(12):
            rev = rev_y*SEASON[m]/12
            cf = rev - rev*var_rate - fix_y/12 - debt/12
            flows.append(cf)
    cum, run_t = [], F(0)
    for f in flows:
        run_t += f
        cum.append(run_t)
    return flows, cum, (n, monthly_burn, total_pre)

# ---------------------------------------------------------------- exit cross-check
def exit_values(site, ops, noi_stabilized):
    appreciation = site.price*(1+ops.appreciation)**ops.hold_years
    by_cap = {c: noi_stabilized*(1+INFLATE)**ops.hold_years / (F(c,100)) for c in (6,7,8,9)}
    return appreciation, by_cap

# ---------------------------------------------------------------- correlated cases
def correlated(demand):
    """One demand factor moves every revenue driver together, which is how reality works."""
    d = F(demand)
    return dict(WIN,
                activations=max(0, int(round(10*float(d)))),
                activation_fee=F(72_000)*d,
                resid_occ=min(F(1), F(70,100)*(1+(d-1)*F(7,10))),
                prod_days=max(0, int(round(45*float(d)))),
                retreats=max(0, int(round(4*float(d)))))

if __name__ == "__main__":
    ops = replace(Ops(), **WIN)
    site, mode = KONA, "buy"

    print("="*88)
    print("FIX 1 & 2 — the pre-opening hole, and what you actually have to fund")
    print("="*88)
    flows, cum, (n, burn, pre) = cash_curve(site, ops, mode)
    trough = min(cum); trough_m = cum.index(trough)
    print(f"  pre-opening: {n} months at {money(burn)}/mo = {money(pre)} of burn before $1 of revenue")
    print(f"\n  first model said equity required ......... {money(site.price*(1-ops.ltv)+ops.capex)}")
    print(f"  peak cumulative cash deficit ............ {money(-trough)}  (month {trough_m})")
    print(f"  understated by ........................... {money(-trough - (site.price*(1-ops.ltv)+ops.capex))}")
    first_pos = next((i for i,c in enumerate(cum) if c > trough and i > trough_m and c >= 0), None)
    print(f"  months to cumulative break-even .......... {first_pos if first_pos else '> 4 years'}")
    print("\n  month-by-month cumulative cash, first 30 months:")
    for i in range(0, 30, 3):
        bar = "#" * max(0, int(float(-cum[i])/40000)) if cum[i] < 0 else ""
        print(f"    m{i:>2}  {money(cum[i]):>13}  {bar}")

    print("\n" + "="*88)
    print("FIX 3 — exit: does the BUSINESS add terminal value, or just the house?")
    print("="*88)
    base = run(site, ops, mode)
    appr, caps = exit_values(site, ops, base.noi)
    print(f"  stabilized NOI today {money(base.noi)}; in year 10 with 3% inflation "
          f"{money(base.noi*(1+INFLATE)**10)}")
    print(f"\n  exit as a HOUSE (3%/yr appreciation) ......... {money(appr)}")
    for c, v in caps.items():
        verdict = "business adds value" if v > appr else "house is worth more empty"
        print(f"  exit as a BUSINESS at a {c}% cap ............. {money(v):>12}   {verdict}")
    print("""
  A 6% cap on a single-asset, owner-operated, seasonal creator venue in a hurricane
  zone is not a real cap rate. Boutique hospitality trades 8-10%. At 9% the business
  is worth LESS than the house, which means the operating story adds no terminal
  value and you are underwriting a residential appreciation bet with extra steps.""")

    print("\n" + "="*88)
    print("FIX 4 — correlated downside. Drivers do not move one at a time.")
    print("="*88)
    print(f"  {'demand factor':>14}{'gross rev':>13}{'NOI':>11}{'DSCR':>7}{'IRR':>9}{'NPV@12%':>13}{'NPV@20%':>13}")
    for d in ("0.5","0.7","0.85","1.0","1.15","1.3"):
        o = replace(Ops(), **correlated(d))
        b = run(site, o, mode)
        _,_,fl,_ = schedule(site, o, mode, shield_usable=True)
        print(f"  {d:>14}{money(b.gross):>13}{money(b.noi):>11}{float(b.dscr):>7.2f}"
              f"{calc.irr(fl)*100:>8.2f}%{money(calc.npv(F(12,100),fl)):>13}"
              f"{money(calc.npv(F(20,100),fl)):>13}")
    print("""
  The one-at-a-time tornado said -25% on activations still returned +1.09%. Moving
  the drivers together at 0.7 demand is a different business entirely. That gap is
  the single most common way a model flatters a plan.""")
