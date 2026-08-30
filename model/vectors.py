"""Reference vectors: the exact model's answers, for validating the browser calculator."""
import json
from dataclasses import replace
from fractions import Fraction as F
import calc
from model import *
from dcf import schedule
from pro import WIN

CASES = {
 "oahu_base":      (OAHU, "buy",   {}, False),
 "oahu_lease":     (OAHU, "lease", {}, True),
 "kona_base":      (KONA, "buy",   {}, True),
 "kona_lease":     (KONA, "lease", {}, True),
 "kona_win":       (KONA, "buy",   WIN, True),
 "kona_win_low":   (KONA, "buy",   dict(WIN, activations=4), True),
 "kona_win_hi":    (KONA, "buy",   dict(WIN, activations=14, resid_rate=F(8000)), True),
}
out = {}
for name,(site,mode,kw,shield) in CASES.items():
    o = replace(Ops(), **kw)
    b = run(site, o, mode)
    _,rows,fl,ex = schedule(site, o, mode, shield_usable=shield)
    out[name] = dict(
        site=site.name, mode=mode,
        gross=float(b.gross), noi=float(b.noi), total_cost=float(b.total_cost),
        bednights=float(b.used), dscr=(float(b.dscr) if b.dscr else None),
        debt=float(b.debt), equity=float(b.equity), net=float(b.net),
        irr=calc.irr(fl), npv12=float(calc.npv(F(12,100), fl)),
        y1=float(rows[0][1]), y3=float(rows[2][1]),
    )
print(json.dumps(out, indent=1))
