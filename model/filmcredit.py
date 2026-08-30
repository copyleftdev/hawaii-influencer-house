"""What HRS 235-17 is actually worth to this business.

Key statutory facts (verified against the current section text and the 2026 Film Office guidance):
  * The credit is REFUNDABLE and is claimed by the PRODUCTION COMPANY, not the venue.
  * "Rentals and fees for use of local facilities and locations" and "rentals of vehicles
    and lodging for cast and crew" and "airfare for flights to or from Hawaii" are all
    qualified production costs.
  * "Commercial" EXPRESSLY excludes "an advertising message with Internet-only distribution."
  * "Qualified production" EXPRESSLY excludes productions "produced primarily for
    industrial, corporate, institutional, or other private purposes."
  => A TikTok/IG brand campaign shot at the house is NOT a qualified production.
  => A music video, short film, streaming series/pilot/special, or a TV-distributed
     commercial shot at the house IS. The house is then a qualified EXPENSE of that
     production, and its invoice is 22-32% subsidised by the State.
"""
from fractions import Fraction as F
import calc
from calc import E, sym, mul, sub, money, pct
from model import OAHU, KONA, Ops, GET

RATES = {
    "Oahu, base":                 F(22,100),
    "Oahu, 80% local-hire uplift":F(27,100),
    "Neighbor island, base":      F(27,100),
    "Neighbor island, uplift":    F(32,100),
}

def gross_for_net(net, credit):
    """Invoice you can charge so the production's AFTER-CREDIT cost equals `net`.
       Solve  G*(1-c) = net   for G."""
    r = calc.solve_linear(mul(E(1-credit), sym("G")), E(net), "G")
    s = r["solutions"][0]
    return F(int(s["numerator"]), int(s["denominator"]))

def report():
    ops = Ops()
    net = ops.prod_day_rate           # what an unsubsidised customer would pay: $4,500/day
    print("="*82)
    print("The credit is a DEMAND subsidy, not a supply subsidy.")
    print(f"Holding the production's out-of-pocket cost fixed at {money(net)}/day:")
    print("="*82)
    print(f"  {'credit regime':<32}{'rate':>7}{'you can invoice':>18}{'uplift vs. no credit':>22}")
    base = None
    for label, c in RATES.items():
        g = gross_for_net(net, c)
        if base is None: base = g
        print(f"  {label:<32}{pct(c,0):>7}{money(g,2):>18}{pct(g/net-1,1):>22}")
    oahu_g = gross_for_net(net, RATES["Oahu, base"])
    bi_g   = gross_for_net(net, RATES["Neighbor island, uplift"])
    print(f"\n  Neighbor-island-with-uplift premium over Oahu-base: {pct(bi_g/oahu_g-1,2)}")
    print(f"  On {ops.prod_days} location days/yr that is {money((bi_g-oahu_g)*ops.prod_days)} of extra")
    print(f"  gross revenue for the SAME cost to the customer — paid by the State, not the client.")

    print("\n" + "="*82)
    print("Threshold check: the customer must clear $100,000 of Hawaii spend to claim anything.")
    print("="*82)
    for label, c in [("Oahu, base", RATES["Oahu, base"]), ("Neighbor island, uplift", RATES["Neighbor island, uplift"])]:
        print(f"  {label:<32} credit on a $100,000 shoot = {money(F(100_000)*c)}")
    print("  => single-day creator shoots never qualify. Multi-week series/music-video")
    print("     blocks do. That dictates who you sell location days to.")

    print("\n" + "="*82)
    print("What the credit is NOT worth to you")
    print("="*82)
    print("  The house's own revenue is NOT a qualified production cost to the house.")
    print("  If the house itself produced a qualifying show, it could claim on its own")
    print("  spend - but its rent/mortgage is not production spend, and a branded social")
    print("  campaign is statutorily excluded. Budget $0 of direct credit to the venue.")

if __name__ == "__main__":
    report()
