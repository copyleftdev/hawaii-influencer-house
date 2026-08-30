"""Hawaii influencer-house financial model — capacity-constrained.

The house is a fixed pool of bed-nights. Every revenue engine consumes them.
Nothing may be sold twice. All money exact (Fraction); amortization/NPV/IRR via agent-calc.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as F
import calc
from calc import money, pct

def P(s):
    return F(s) / 100

GET       = P("4.5")     # statewide GET incl. county surcharge, on ALL gross receipts
TAT       = P("14")      # 11% state (2026) + 3% county, on lodging under 180 consecutive days
DAYS      = 365

# ------------------------------------------------------------------ site

@dataclass(frozen=True)
class Site:
    name: str; county: str
    price: F; lease_monthly: F
    film_credit: F; film_credit_uplift: F
    insurance: F; utilities: F; maintenance_pct: F
    proptax_resid: F; proptax_hotel: F

OAHU = Site("Oahu — North Shore", "Honolulu",
            F(4_000_000), F(18_000), P("22"), P("27"),
            F(38_000), F(42_000), F("1.5")/100,
            F(1_000_000)*F("4.50")/1000 + F(3_000_000)*F("11.40")/1000,   # Residential A
            F(4_000_000)*F("13.90")/1000)                                 # Hotel/Resort

KONA = Site("Hawaii Island — Kona", "Hawaii",
            F(2_600_000), F(12_000), P("27"), P("32"),
            F(30_000), F(34_000), F("1.5")/100,
            F(2_600_000)*F("11.10")/1000,
            F(2_600_000)*F("11.55")/1000)

# ------------------------------------------------------------------ ops

@dataclass(frozen=True)
class Ops:
    beds: int = 10
    # --- engines, each expressed in the bed-nights it consumes ---
    resid_occ: F = P("70")        # share of the bed-nights LEFT OVER after the others
    resid_rate: F = F(6_500)      # $/seat-month
    term_180_plus: bool = True    # 180+ day terms: TAT-exempt, GET only

    activations: int = 8          # whole-house brand takeovers
    activation_days: int = 5
    activation_fee: F = F(55_000)
    activation_direct: F = P("35")

    prod_days: int = 30           # location days sold to qualified productions
    prod_day_rate: F = F(4_500)
    prod_direct: F = P("15")

    retreats: int = 4
    retreat_days: int = 8
    retreat_seats: int = 10
    retreat_price: F = F(7_500)
    retreat_direct: F = P("40")

    # --- fixed cost ---
    staff_loaded: F = F(265_000)
    founder_comp: F = F(120_000)
    marketing: F = F(60_000)
    legal_accounting: F = F(35_000)
    software_gear: F = F(24_000)
    consumables_bednight: F = F(11)
    payment_fees: F = P("3")

    # --- capital ---
    ltv: F = P("70"); rate: F = F("7.25")/100; term_months: int = 360
    capex: F = F(610_000)
    capex_short_life: F = F(85,100)   # share of build-out in <=15yr classes
    appreciation: F = P("3"); sale_costs: F = P("6"); hold_years: int = 10
    exit_cap: F = P("6")

# ------------------------------------------------------------------ engine ledger

def engines(ops: Ops):
    """Return per-engine (gross, direct cost, bed-nights consumed)."""
    cap = F(ops.beds * DAYS)
    e = {}
    e["Brand activations"] = (F(ops.activations)*ops.activation_fee,
                              F(ops.activations)*ops.activation_fee*ops.activation_direct,
                              F(ops.activations*ops.activation_days*ops.beds))
    e["Cohort retreats"]   = (F(ops.retreats*ops.retreat_seats)*ops.retreat_price,
                              F(ops.retreats*ops.retreat_seats)*ops.retreat_price*ops.retreat_direct,
                              F(ops.retreats*ops.retreat_days*ops.retreat_seats))
    e["Production days"]   = (F(ops.prod_days)*ops.prod_day_rate,
                              F(ops.prod_days)*ops.prod_day_rate*ops.prod_direct,
                              F(ops.prod_days*ops.beds))
    used = sum(v[2] for v in e.values())
    remaining = cap - used
    if remaining < 0:
        raise ValueError(f"over-sold capacity by {-remaining} bed-nights")
    resid_bn = remaining * ops.resid_occ
    resid_gross = resid_bn / F(365,12) * ops.resid_rate   # 365/12 nights per seat-month
    e["Creator residencies"] = (resid_gross, F(0), resid_bn)
    return e, cap, used + resid_bn

# ------------------------------------------------------------------ P&L

@dataclass
class Result:
    label: str; site: Site; ops: Ops; mode: str
    rev: dict; cost: dict; eng: dict
    gross: F; total_cost: F; noi: F; debt: F; net: F
    dscr: F | None; equity: F; cap: F; used: F

def run(site: Site, ops: Ops, mode: str, proptax="resid", ramp: F = F(1)) -> Result:
    eng, cap, used = engines(ops)
    rev  = {k: v[0]*ramp for k, v in eng.items()}
    gross = sum(rev.values(), F(0))
    bednights_sold = used*ramp

    c = {}
    if mode == "buy":
        equity = site.price*(1-ops.ltv) + ops.capex
        debt = calc.amortize(site.price*ops.ltv, ops.rate, ops.term_months, 12)*12
        c["Property tax"] = site.proptax_resid if proptax=="resid" else site.proptax_hotel
        c["Insurance"] = site.insurance
        c["Maintenance & reserves"] = site.price*site.maintenance_pct
    else:
        equity = ops.capex; debt = F(0)
        c["Master lease"] = site.lease_monthly*12
        c["Insurance (contents/GL)"] = site.insurance/2
        c["Maintenance & reserves"] = site.price*site.maintenance_pct/3

    c["Utilities & connectivity"] = site.utilities
    c["Staff (loaded)"] = ops.staff_loaded
    c["Founder compensation"] = ops.founder_comp
    c["Marketing & booking"] = ops.marketing
    c["Legal, GET/TAT, CPA"] = ops.legal_accounting
    c["Software & gear service"] = ops.software_gear
    c["Consumables & housekeeping"] = bednights_sold*ops.consumables_bednight
    c["Engine direct costs"] = sum((v[1] for v in eng.values()), F(0))*ramp
    c["GET @ 4.5% of gross"] = gross*GET
    c["TAT @ 14% of lodging"] = F(0) if ops.term_180_plus else rev["Creator residencies"]*TAT
    c["Payment/platform fees"] = gross*ops.payment_fees

    total = sum(c.values(), F(0))
    noi = gross - total
    net = noi - debt
    return Result(f"{site.name} — {mode}", site, ops, mode, rev, c, eng,
                  gross, total, noi, debt, net, (noi/debt if debt else None),
                  equity, cap, used)

def show(r: Result):
    print(f"\n{'='*78}\n{r.label}\n{'='*78}")
    print(f"{'REVENUE':<32}{'gross':>13}{'bed-nights':>12}{'$/bed-night':>14}{'net $/bn':>11}")
    for k,(g,d,bn) in sorted(r.eng.items(), key=lambda x: -( (x[1][0]-x[1][1])/x[1][2] if x[1][2] else 0)):
        yld = (g-d)/bn if bn else F(0)
        print(f"  {k:<30}{money(g):>13}{int(bn):>12,}{money(g/bn if bn else 0):>14}{money(yld):>11}")
    print(f"  {'GROSS REVENUE':<30}{money(r.gross):>13}{int(r.used):>12,}"
          f"   utilization {pct(r.used/r.cap,1)}")
    print("\nCOSTS")
    for k,v in r.cost.items():
        if v: print(f"  {k:<40}{money(v):>14}")
    print(f"  {'TOTAL COST':<40}{money(r.total_cost):>14}")
    print(f"\n  {'NOI (before debt)':<40}{money(r.noi):>14}   margin {pct(r.noi/r.gross,1)}")
    if r.debt:
        print(f"  {'Debt service':<40}{money(r.debt):>14}   DSCR {float(r.dscr):.2f}")
    print(f"  {'NET CASH FLOW':<40}{money(r.net):>14}")
    print(f"  {'Equity in':<40}{money(r.equity):>14}   cash-on-cash {pct(r.net/r.equity)}")
