# The Hawaii House Question

**Can a ten-bedroom creator house in Hawaii pay for itself?**

### → [Read it](https://copyleftdev.github.io/hawaii-influencer-house/) · [Full report](https://copyleftdev.github.io/hawaii-influencer-house/verdict.html) · [Interactive sandbox](https://copyleftdev.github.io/hawaii-influencer-house/calculator.html)

[![Tip my tokens](https://tokentip.to/badge/copyleftdev.svg?logo=1)](https://tokentip.to/@copyleftdev)
[![License: MIT](https://img.shields.io/badge/License-MIT-14615A.svg)](LICENSE)

A complete feasibility model — two islands, buy against lease, four revenue engines, and
every tax line the State of Hawaii actually charges. Every figure is exact rational
arithmetic produced by [`agent-calc`](https://github.com/copyleftdev). **No number in this
repository was produced by a language model.**

> Powered by **Bento** — every figure carries its own arithmetic.

---

## The answer

**Rent from influencers cannot carry the building.** Not on either island, not buying, not
leasing. Every configuration needs impossible occupancy:

| Configuration | Fixed cost | Seat-months needed | Occupancy | |
|---|--:|--:|--:|---|
| Oʻahu — buy | $911,911 | 160.6 | **133.8%** | impossible |
| Oʻahu — lease | $801,000 | 141.1 | **117.6%** | impossible |
| Hawaiʻi Island — buy | $784,847 | 138.2 | **115.2%** | impossible |
| Hawaiʻi Island — lease | $710,000 | 125.0 | **104.2%** | impossible |

*(the house has 120 seat-months to sell)*

Covering costs on rent alone needs **$107,000–$136,000 per creator per year**. Creators
who can pay that do not need a shared house.

**One configuration clears a 12% hurdle**: Hawaiʻi Island, purchased, 30-day service
terms, location days priced against the film credit, ten brand takeovers a year at $72k —
**12.93% ten-year IRR, 2.78× debt coverage**. Oʻahu is negative in every variant.

But that is the **82nd percentile**, not the expected case. Across 600 correlated paths the
median loses money and there is a **27% chance of failing to cover debt service**.

**It is not an influencer house.** It is a branded-content production venue that keeps a
resident roster as inventory. Brand activations are 43% of revenue and every dollar of
return sits on them.

---

## Two legal facts that decide it before any spreadsheet

**The short-stay market is closed on Oʻahu.** Ordinance 22-7 set a 90-day minimum; a
federal court permanently enjoined it in December 2023, so enforcement runs on the older
30-day standard. Nothing shorter is available outside resort zoning. Maui's Ordinance 5909
phases out ~6,200 apartment-district vacation rentals by 2029–2031.

**The film credit excludes exactly what you were going to make.** HRS §235-17 pays 22%
(Oʻahu) / 27% (neighbor islands), plus five points for ≥80% local hires under Act 185
(2026) — refundable, generous, and disqualifying:

> **"Commercial"** … *does not include an advertising message with Internet-only
> distribution.*
>
> **"Qualified production"** … does not include … *productions produced primarily for
> industrial, corporate, institutional, or other private purposes.*
>
> — HRS §235-17(o)

A TikTok or Instagram brand campaign is statutorily excluded. But *lodging for cast and
crew*, *rentals and fees for use of local facilities*, and *airfare to Hawaii* are all
qualified costs. So the move is: **don't be the taxpayer, be the qualified expense.** When
a music video or streaming series rents the house, they claim the credit on your invoice —
which lets a neighbor island invoice **14.71% more than Oʻahu for identical customer cost**.

---

## The capacity insight

A house is a fixed pool of bed-nights. Nothing can be sold twice. Priced per bed-night
consumed, the hierarchy is unambiguous:

| Engine | Net $/bed-night |
|---|--:|
| Brand activations | $936 |
| Cohort retreats | $563 |
| Production location days | $563 |
| **Creator residencies** | **$214** |

Housing influencers is the *least* productive use of the asset — and it occupies most of
the calendar. Residency is not the business; it is the inventory that makes the business
sellable.

---

## Running it

Requires [`agent-calc`](https://github.com/copyleftdev) on `PATH`, Python 3.11+, and Node
22+ for the browser-port verification.

```sh
cd model
python3 breakeven.py      # can rent alone carry it (no), and what rent would
python3 stacked.py        # the scenario ladder, 0 -> 5
python3 filmcredit.py     # what HRS 235-17 is worth, and to whom
python3 structures.py     # term length, GET pyramiding, opportunity zone
python3 sensitivity.py    # null hypothesis, tornado, what-would-have-to-be-true
python3 pro.py            # the underwriter pass: pre-opening, cash curve, correlated downside
python3 mc2.py            # 600-path Monte Carlo, two exit routes
node verify.js            # browser port vs the exact model
```

| File | What it answers |
|---|---|
| `model/calc.py` | agent-calc client — amortize, NPV, IRR, affine solve, exact decimals |
| `model/model.py` | sites, assumptions, bed-night capacity ledger, single-year P&L |
| `model/breakeven.py` | can rent alone carry it; required rent; mix breakeven |
| `model/dcf.py` | 10-year levered after-tax DCF with cost segregation, recapture, exit |
| `model/filmcredit.py` | HRS §235-17 pricing analysis |
| `model/structures.py` | term-length trade, GET pyramiding, opportunity zone |
| `model/sensitivity.py` | null hypothesis, tornado, required conditions |
| `model/pro.py` | the four omissions an underwriter would flag |
| `model/mc2.py` | correlated Monte Carlo across two exit routes |
| `model/engine.js` | browser port, validated against the exact model |
| `verdict.html` | the written analysis |
| `calculator.html` | live sandbox — turn the knobs yourself |

Open `verdict.html` or `calculator.html` directly in a browser; both are self-contained.

They are authored as *fragments* (no `<html>`/`<head>`) so the same files can be published
as Claude Artifacts, where the host supplies the document shell. `build.py` supplies an
equivalent shell plus canonical/Open Graph/JSON-LD and emits `site/` for GitHub Pages:

```sh
python3 build.py      # -> site/
```

---

## Method

Every load-bearing number goes through `agent-calc` as exact rational arithmetic —
amortization schedules, NPV, IRR, and all breakeven solves. Composition happens in Python
`Fraction`, so no floating point enters the chain. Legal figures are read from the current
text of HRS §235-17 and §237-16.5 and the 2026 Hawaiʻi Film Office guidance under Act 185.

The browser port in `engine.js` mirrors the Python model and is checked against reference
vectors generated from it. Worst relative error **1.9 × 10⁻⁸** — float64 rounding in the
discounting chain, fractions of a cent on a million-dollar NPV.

### Findings about method, not about Hawaii

Four of these cost real analytical blood and generalize past this project:

- **Rank simulations on NPV, not IRR.** IRR is undefined when cash flows never change
  sign, which happens on precisely the worst paths. Ranking on IRR silently deleted
  127 of 600 paths — all bad ones — and reported a healthier business than existed.
- **"Equity in" is not the capital requirement.** The peak cumulative cash deficit was
  $2,017,029 against a $1,390,000 down payment plus capex. Understated by 45%.
- **A trough at the edge of your window is not a trough.** The downside case reported a
  finite funding need that was just where the model stopped looking. It never recovers.
- **The residential value is a floor under the operating business** — effectively a free
  put, and the strongest argument for buying over leasing. A cap-rate exit alone is
  leveraged to NOI and is *worse* than the house on weak paths; model `max(house, business)`.

---

## Limits

Revenue assumptions are judgement, not data. There is no public comparable for a Hawaii
creator-production house, so the brand-activation pipeline is the load-bearing guess and is
treated as such throughout — the model's real output is a ranked list of the four numbers
worth spending money to learn, three of which can be tested for under 3% of the capital at
risk.

Tax treatment is directional and depends on facts a Hawaii CPA must confirm, particularly
material participation, the Reg. §1.469-1T(e)(3)(ii)(B) services exception, and county
property classification.

**This is a model, not advice** — financial, legal, or tax.

---

## License

MIT © 2026 copyleftdev
