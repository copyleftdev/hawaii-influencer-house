"""10-year levered after-tax DCF: buy vs. lease. IRR and NPV via agent-calc."""
from fractions import Fraction as F
import calc
from calc import money, pct
from model import *
from breakeven import fixed_costs

RAMP     = [F(55,100), F(80,100)] + [F(1)]*8      # revenue as share of steady-state plan
GROWTH   = F(3,100)
INFLATE  = F(3,100)
TAX_ORD  = F(40,100)      # blended fed (37% less QBI) + Hawaii 11%, top-bracket owner
TAX_1250 = F(25,100) + F("7.25")/100
TAX_LTCG = F(20,100) + F("3.8")/100 + F("7.25")/100
LAND     = {"Honolulu": F(40,100), "Hawaii": F(30,100)}
COSTSEG  = F(25,100)      # share of building basis reclassified to <=15yr, bonus-eligible
CAPEX_5YR= F(85,100)      # default; overridden per-scenario by ops.capex_short_life

_SCHED = {}
def sched(principal, rate, term=360):
    k = (principal, rate, term)
    if k not in _SCHED:
        # round to cents once: the exact schedule carries ~1000-digit rationals and
        # every downstream sum on them is slow. A real loan is denominated in cents.
        _SCHED[k] = [tuple(calc.cents(x) for x in row)
                     for row in calc.amort_schedule(principal, rate, term, 12)]
    return _SCHED[k]

def year_interest(principal, rate, year, term=360):
    s = sched(principal, rate, term)
    return sum((s[m][0] for m in range(12*(year-1), 12*year)), F(0))

def loan_balance(principal, rate, months_paid, term=360):
    if months_paid == 0:
        return principal
    return sched(principal, rate, term)[months_paid-1][2]

def schedule(site, ops, mode, shield_usable=True, proptax="resid"):
    base = run(site, ops, mode, proptax)
    fx, fxd = fixed_costs(site, ops, mode, proptax)
    tat_cost = F(0) if ops.term_180_plus else base.rev["Creator residencies"]*TAT
    var_rate = (base.gross*(GET+ops.payment_fees)
                + sum((v[1] for v in base.eng.values()), F(0))
                + base.used*ops.consumables_bednight
                + tat_cost) / base.gross   # variable cost per $ of revenue
    debt = fxd.get("debt", F(0))
    fixed_ex_debt = fx - debt

    # ---- depreciation ----
    if mode == "buy":
        bldg = site.price*(1-LAND[site.county])
        bonus_y1 = bldg*COSTSEG + ops.capex*ops.capex_short_life
        straight = (bldg*(1-COSTSEG) + ops.capex*(1-ops.capex_short_life))/39
    else:
        bonus_y1 = ops.capex*ops.capex_short_life
        straight = ops.capex*(1-ops.capex_short_life)/10

    rows, flows = [], [-base.equity]
    carry = F(0)
    accum_1250, accum_1245 = F(0), bonus_y1 if mode=="buy" else F(0)
    principal = site.price*ops.ltv if mode=="buy" else F(0)
    for y in range(1, ops.hold_years+1):
        g = (1+GROWTH)**(y-1)
        rev  = base.gross*RAMP[y-1]*g
        varc = rev*var_rate
        fixc = fixed_ex_debt*(1+INFLATE)**(y-1)
        ebitda = rev - varc - fixc
        interest = year_interest(principal, ops.rate, y) if mode == "buy" else F(0)
        dep = (bonus_y1 if y==1 else F(0)) + straight
        accum_1250 += straight
        taxable = ebitda - interest - dep + carry
        if taxable < 0:
            carry = taxable if not shield_usable else F(0)
            tax = taxable*TAX_ORD if shield_usable else F(0)   # negative = refund/offset
        else:
            carry = F(0); tax = taxable*TAX_ORD
        cf = ebitda - debt - tax
        flows.append(calc.cents(cf))
        rows.append((y, rev, ebitda, debt, dep, taxable, tax, cf))

    # ---- exit ----
    if mode == "buy":
        val = site.price*(1+ops.appreciation)**ops.hold_years
        netsale = val*(1-ops.sale_costs)
        bal = loan_balance(principal, ops.rate, 12*ops.hold_years)
        basis = site.price + ops.capex - accum_1250 - accum_1245
        gain = netsale - basis
        t1245 = min(accum_1245, max(F(0), gain))*TAX_ORD
        rem = max(F(0), gain - accum_1245)
        t1250 = min(accum_1250, rem)*TAX_1250
        tcap = max(F(0), rem - accum_1250)*TAX_LTCG
        proceeds = netsale - bal - t1245 - t1250 - tcap
        flows[-1] = calc.cents(flows[-1] + proceeds)
        exit_detail = dict(value=val, netsale=netsale, balance=bal, basis=basis, gain=gain,
                           t1245=t1245, t1250=t1250, tcap=tcap, proceeds=proceeds)
    else:
        exit_detail = None
    return base, rows, flows, exit_detail

def show(site, ops, mode, shield_usable=True, proptax="resid"):
    base, rows, flows, ex = schedule(site, ops, mode, shield_usable, proptax)
    tag = "shield usable" if shield_usable else "losses suspended (passive)"
    print(f"\n{'='*94}\n{site.name} — {mode.upper()}   [{tag}]\n{'='*94}")
    print(f"{'yr':>3}{'revenue':>13}{'EBITDA':>12}{'debt svc':>11}{'deprec.':>13}"
          f"{'taxable':>13}{'tax':>12}{'net CF':>13}")
    for y,rev,ebitda,d,dep,tx,t,cf in rows:
        print(f"{y:>3}{money(rev):>13}{money(ebitda):>12}{money(d):>11}{money(dep):>13}"
              f"{money(tx):>13}{money(t):>12}{money(cf):>13}")
    if ex:
        print(f"\n  exit: value {money(ex['value'])}  net of costs {money(ex['netsale'])}"
              f"  loan {money(ex['balance'])}")
        print(f"        basis {money(ex['basis'])}  gain {money(ex['gain'])}"
              f"  recapture 1245 {money(ex['t1245'])} / 1250 {money(ex['t1250'])}"
              f"  cap gains {money(ex['tcap'])}")
        print(f"        NET SALE PROCEEDS {money(ex['proceeds'])}")
    eq = -flows[0]
    print(f"\n  equity in {money(eq)}   10-yr IRR {calc.irr(flows)*100:>6.2f}%"
          f"   NPV@12% {money(calc.npv(F(12,100), flows))}"
          f"   MoIC {float(sum(flows[1:])/eq):.2f}x")
    return flows

if __name__ == "__main__":
    ops = Ops()
    for site in (OAHU, KONA):
        for mode in ("buy","lease"):
            show(site, ops, mode)
    print("\n\n### stress: material participation fails, losses suspended ###")
    show(KONA, ops, "buy", shield_usable=False)
