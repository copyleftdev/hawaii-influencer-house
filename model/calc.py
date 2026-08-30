"""Thin exact-arithmetic client for agent-calc.

Every load-bearing financial number in this model is produced by agent-calc and
returned as an exact Fraction. Python's Fraction/int arithmetic is itself exact,
so composing results here does not reintroduce floating point.
"""
import json
import subprocess
from fractions import Fraction

BIN = "agent-calc"


def _run(domain, req):
    p = subprocess.run([BIN, domain], input=json.dumps(req), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"agent-calc {domain} failed rc={p.returncode}: {p.stderr[:400]}")
    return json.loads(p.stdout)


def E(x):
    """Encode a Fraction/int/str-decimal as an exact agent-calc Expr leaf."""
    f = Fraction(x) if not isinstance(x, Fraction) else x
    if f.denominator == 1:
        return {"kind": "integer", "value": str(f.numerator)}
    return {"kind": "rational", "numerator": str(f.numerator), "denominator": str(f.denominator)}


def _frac(node):
    return Fraction(int(node["numerator"]), int(node["denominator"]))


def ev(expr):
    """Evaluate an exact rational expression tree."""
    return _frac(_run("eval", {"expr": expr})["exact"])


def add(*xs):
    n = xs[0]
    for x in xs[1:]:
        n = {"kind": "add", "left": n, "right": x}
    return n


def sub(a, b):
    return {"kind": "sub", "left": a, "right": b}


def mul(*xs):
    n = xs[0]
    for x in xs[1:]:
        n = {"kind": "mul", "left": n, "right": x}
    return n


def div(a, b):
    return {"kind": "div", "left": a, "right": b}


_AMORT_CACHE = {}


def amortize(principal, annual_rate, periods, periods_per_year=12):
    """Exact level payment on a fully amortizing loan. Memoized: the exact
    360-period response is large, and the DCF asks for the same loan repeatedly."""
    key = (principal, annual_rate, periods, periods_per_year)
    if key in _AMORT_CACHE:
        return _AMORT_CACHE[key]
    r = _run("finance", {
        "intent": "amortize",
        "principal": E(principal),
        "annual_rate": E(annual_rate),
        "periods": periods,
        "periods_per_year": periods_per_year,
    })
    _AMORT_CACHE[key] = _frac(r["payment"])
    return _AMORT_CACHE[key]


def npv(rate, flows):
    """NPV of flows where flows[0] is at t=0."""
    r = _run("finance", {
        "intent": "net_present_value",
        "rate": E(rate),
        "cash_flows": [E(f) for f in flows],
        "decimal_places": 6,
    })
    return _frac(r["exact"])


def irr(flows, tolerance=1e-10):
    r = _run("finance", {
        "intent": "irr",
        "cash_flows": [E(f) for f in flows],
        "tolerance": tolerance,
    })
    if r.get("status") == "error":
        # no sign change in the bracket -> IRR is undefined, not zero. Say so.
        return None
    return r["approximate_f64"]


def solve_linear(lhs, rhs, variable):
    """Solve an exact affine equation lhs == rhs for `variable`."""
    r = _run("solve", {"intent": "solve", "equation": {"left": lhs, "right": rhs}, "variable": variable})
    return r


def sym(name):
    return {"kind": "symbol", "name": name}


def money(f, places=0):
    """Exact half-up decimal rendering of a Fraction as dollars."""
    neg = f < 0
    f = -f if neg else f
    scale = 10 ** places
    n = (f * scale * 2 + 1) // 2  # exact half-up on integers
    s = f"{n // scale:,}"
    if places:
        s += "." + str(n % scale).rjust(places, "0")
    return ("-$" if neg else "$") + s


def pct(f, places=2):
    v = f * 100
    scale = 10 ** places
    n = (abs(v) * scale * 2 + 1) // 2
    sign = "-" if v < 0 else ""
    return f"{sign}{n // scale}.{str(n % scale).rjust(places, '0')}%"


def amort_schedule(principal, annual_rate, periods, periods_per_year=12):
    """Exact per-period (interest, principal_paid, balance)."""
    r = _run("finance", {
        "intent": "amortize",
        "principal": E(principal),
        "annual_rate": E(annual_rate),
        "periods": periods,
        "periods_per_year": periods_per_year,
    })
    return [(_frac(e["interest"]), _frac(e["principal_paid"]), _frac(e["balance"]))
            for e in r["schedule"]]


def cents(f):
    """Round an exact Fraction to whole cents (half-up), staying exact."""
    neg = f < 0
    f = -f if neg else f
    n = (f * 200 + 1) // 2
    v = Fraction(n, 100)
    return -v if neg else v
