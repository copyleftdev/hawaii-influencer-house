#!/usr/bin/env python3
"""Wrap the page fragments into full documents and emit the static site into site/.

verdict.html and calculator.html are authored as fragments so the same files can be
published as Claude Artifacts, where the host supplies the document shell. This build
supplies an equivalent shell plus canonical/OG/JSON-LD so the pages stand alone.
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "site"
BASE = "https://copyleftdev.github.io/hawaii-influencer-house"
REPO = "https://github.com/copyleftdev/hawaii-influencer-house"
AUTHOR = "copyleftdev"
UPDATED = "2026-08-29"

PAGES = [
    dict(src=ROOT / "pages/index.html", out="index.html",
         name="The Hawaii House Question",
         desc="Can a ten-bedroom creator house in Hawaii pay for itself? An exact-arithmetic "
              "feasibility model across two islands, buy against lease, with every Hawaii tax "
              "line and the film credit that excludes social content.",
         kind="WebPage"),
    dict(src=ROOT / "verdict.html", out="verdict.html",
         name="The Hawaii House Question — full report",
         desc="Eight sections on whether a Hawaii creator house pays for itself: short-term "
              "rental law, the bed-night capacity ledger, buy against lease, entity structure, "
              "and an underwriter's pass that finds four holes in the first seven.",
         kind="TechArticle"),
    dict(src=ROOT / "calculator.html", out="calculator.html",
         name="Creator House Sandbox",
         desc="Live sandbox for the Hawaii creator-house model. Turn the knobs and watch "
              "capacity, P&L, debt coverage, ten-year return and peak funding need recompute.",
         kind="WebApplication"),
]

FAQ = [
    ("Can you run a short-term rental influencer house on Oahu?",
     "No. Ordinance 22-7 set a 90-day minimum; a federal court permanently enjoined it in "
     "December 2023, so enforcement runs on the older 30-day standard. Nothing shorter is "
     "available outside resort zoning. Maui's Ordinance 5909 phases out roughly 6,200 "
     "apartment-district vacation rentals between 2029 and 2031."),
    ("Does the Hawaii film tax credit cover social media content?",
     "No. HRS 235-17(o) excludes advertising with Internet-only distribution, and excludes "
     "productions made primarily for private or corporate purposes. Music videos, short films, "
     "streaming series and TV-distributed commercials do qualify, so the house earns from the "
     "credit as a vendor to those productions, never as the claimant."),
    ("What is the most profitable use of a bed in a creator house?",
     "Brand activations, at $936 net per bed-night. Cohort retreats and production location "
     "days both return $563. Creator residencies return $214 - the least productive use of the "
     "asset, and the one that occupies most of the calendar."),
    ("How much capital does it actually take?",
     "$2,017,029 - the peak cumulative cash deficit, reached in month 21. That is 45% more than "
     "the $1,390,000 down payment plus build-out, because nine months of pre-opening burn and "
     "the operating trough both come before any recovery."),
]

# The Artifact host applies this reset; reproduce it so the pages render identically.
RESET = """    *,::before,::after{box-sizing:border-box}
    html{color-scheme:light dark}
    body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
    img,video{max-width:100%;height:auto}
    [hidden]{display:none!important}"""

TAG = re.compile(r"<(title|link|style)\b[^>]*?(?:/>|>(?:.*?</\1>)?)", re.S | re.I)


def split_fragment(text):
    """Pull <title>, <link> and <style> out of a fragment; return (head_bits, body)."""
    head = []

    def take(m):
        head.append(m.group(0))
        return ""

    body = TAG.sub(take, text)
    title = ""
    for h in head:
        t = re.match(r"<title[^>]*>(.*?)</title>", h, re.S | re.I)
        if t:
            title = t.group(1).strip()
    head = [h for h in head if not re.match(r"<title", h, re.I)]
    return title, head, body.strip()


def jsonld(page, title):
    url = f"{BASE}/{page['out']}".replace("/index.html", "/")
    blocks = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": "The Hawaii House Question",
         "url": BASE + "/", "inLanguage": "en",
         "publisher": {"@type": "Person", "name": AUTHOR, "url": f"https://github.com/{AUTHOR}"}},
        {"@context": "https://schema.org", "@type": page["kind"],
         "name": title, "headline": title, "description": page["desc"], "url": url,
         "inLanguage": "en", "dateModified": UPDATED, "datePublished": UPDATED,
         "license": "https://opensource.org/licenses/MIT",
         "author": {"@type": "Person", "name": AUTHOR, "url": f"https://github.com/{AUTHOR}"},
         "image": f"{BASE}/og-{Path(page['out']).stem}.png",
         "isBasedOn": REPO},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "The Hawaii House Question", "item": BASE + "/"}
        ] + ([] if page["out"] == "index.html" else
             [{"@type": "ListItem", "position": 2, "name": title, "item": url}])},
    ]
    if page["out"] == "index.html":
        blocks.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]})
        blocks.append({"@context": "https://schema.org", "@type": "Dataset",
                       "name": "Hawaii creator-house feasibility model",
                       "description": "Exact-arithmetic financial model of a ten-bedroom creator "
                                      "and production house in Hawaii, computed through agent-calc.",
                       "url": BASE + "/", "license": "https://opensource.org/licenses/MIT",
                       "creator": {"@type": "Person", "name": AUTHOR},
                       "keywords": ["Hawaii", "short-term rental law", "HRS 235-17",
                                    "film tax credit", "financial modeling", "creator economy"]})
    return "\n".join(
        '    <script type="application/ld+json">' + json.dumps(b, separators=(",", ":")) + "</script>"
        for b in blocks)


def build_page(page):
    _fragment_title, head_bits, body = split_fragment(page["src"].read_text())
    title = page["name"]   # the site needs distinct titles; the fragment title serves the Artifact
    url = f"{BASE}/{page['out']}".replace("/index.html", "/")
    og = f"{BASE}/og-{Path(page['out']).stem}.png"
    doc = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <meta name="description" content="{page['desc']}">
    <meta name="author" content="{AUTHOR}">
    <link rel="canonical" href="{url}">
    <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
    <meta name="theme-color" content="#ECEEE9" media="(prefers-color-scheme: light)">
    <meta name="theme-color" content="#0E1513" media="(prefers-color-scheme: dark)">
    <meta property="og:type" content="{'website' if page['out'] == 'index.html' else 'article'}">
    <meta property="og:site_name" content="The Hawaii House Question">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{page['desc']}">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{og}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="{title} — exact-arithmetic feasibility model">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{page['desc']}">
    <meta name="twitter:image" content="{og}">
    <meta name="twitter:label1" content="Method">
    <meta name="twitter:data1" content="Exact rational arithmetic, no LLM-generated figures">
    <meta name="twitter:label2" content="Source">
    <meta name="twitter:data2" content="MIT licensed on GitHub">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='14' font-size='14'>%F0%9F%8C%8B</text></svg>">
    <style>
{RESET}
    </style>
{chr(10).join('    ' + h for h in head_bits)}
{jsonld(page, title)}
</head>
<body>
{body}
</body>
</html>
"""
    (OUT / page["out"]).write_text(doc)
    return title, url


def og_image(stem, title, subtitle):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1200, 630
    ground, ink, accent, muted = "#0E1513", "#E3E8E1", "#58B8AB", "#8A968E"
    img = Image.new("RGB", (W, H), ground)
    d = ImageDraw.Draw(img)
    # decorative bento grid confined to the right edge, faded, so the text column stays clear
    for i in range(3):
        for j in range(2):
            x, y = 828 + i * 124, 150 + j * 200
            d.rounded_rectangle([x, y, x + 100, y + 165], radius=10, outline="#1D3330", width=3)
    d.rectangle([760, 0, 900, H], fill=ground)  # fade the grid out toward the text
    d.rectangle([0, 0, 14, H], fill=accent)
    serif = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf", 68)
    sans = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 27)
    mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 20)
    d.text((70, 78), "FEASIBILITY MODEL", font=mono, fill=accent)
    y = 140
    for line in wrap(title, serif, 700, d):
        d.text((70, y), line, font=serif, fill=ink)
        y += 78
    y += 18
    for line in wrap(subtitle, sans, 690, d):
        d.text((70, y), line, font=sans, fill=muted)
        y += 38
    d.text((70, H - 62), "EXACT ARITHMETIC  ·  POWERED BY BENTO", font=mono, fill=accent)
    img.save(OUT / f"og-{stem}.png", optimize=True)


def wrap(text, font, width, draw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    built = []
    for p in PAGES:
        title, url = build_page(p)
        og_image(Path(p["out"]).stem, title, p["desc"])
        built.append((title, url, p["desc"]))
        print(f"  {p['out']:<18} {title}")

    (OUT / ".nojekyll").write_text("")

    (OUT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in
                  ("GPTBot", "ClaudeBot", "Claude-Web", "anthropic-ai", "PerplexityBot",
                   "Google-Extended", "CCBot", "Applebot-Extended"))
        + f"Sitemap: {BASE}/sitemap.xml\n")

    urls = "".join(
        f"  <url><loc>{u}</loc><lastmod>{UPDATED}</lastmod>"
        f"<changefreq>monthly</changefreq><priority>{'1.0' if u.endswith('/') else '0.8'}</priority>"
        f"</url>\n" for _, u, _ in built)
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")

    (OUT / "llms.txt").write_text(f"""# The Hawaii House Question

> Exact-arithmetic feasibility model asking whether a ten-bedroom creator/production house
> in Hawaii can pay for itself. Every figure is exact rational arithmetic from agent-calc.
> No number was produced by a language model.

## Findings

- Creator rent cannot carry the building in any configuration modelled. All four
  (Oahu/Hawaii Island x buy/lease) require 104%-134% occupancy against a 120 seat-month
  capacity. Breaking even on rent alone needs $107,000-$136,000 per creator per year.
- One configuration clears a 12% hurdle: Hawaii Island, purchased, 30-day service terms,
  location days priced against the film credit, ten brand takeovers a year at $72,000.
  12.93% ten-year IRR, 2.78x debt coverage. Oahu is negative in every variant.
- That case is the 82nd percentile of 600 correlated paths. The median path loses money and
  there is a 27% chance of failing to cover debt service.
- Real capital requirement is $2,017,029 (peak cumulative cash deficit, month 21), not the
  $1,390,000 down payment plus build-out - understated by 45%.
- Per bed-night: brand activations $936, retreats $563, production days $563, creator
  residencies $214. Housing influencers is the least productive use of the asset.

## Law

- Oahu allows nothing under 30 days outside resort zoning. Ordinance 22-7's 90-day minimum
  was permanently enjoined by a federal court in December 2023.
- Maui Ordinance 5909 phases out ~6,200 apartment-district vacation rentals, 2029-2031.
- HRS 235-17 pays 22% (Oahu) / 27% (neighbor islands) refundable, +5% for >=80% local hires
  under Act 185 (2026). But "commercial" excludes advertising with Internet-only
  distribution, and qualified productions exclude those made primarily for private or
  corporate purposes - so social brand campaigns do not qualify. Lodging, location fees and
  airfare ARE qualified costs, so the house should be a vendor to qualifying productions
  rather than the claimant.
- GET is 4.5% on all gross receipts. TAT is 14% (11% state + 3% county) on stays under 180
  consecutive days.

## Pages

- [Home]({BASE}/): the question, the answer, and how it is computed
- [Full report]({BASE}/verdict.html): eight sections including the underwriter's pass
- [Interactive sandbox]({BASE}/calculator.html): change the assumptions and recompute
- [Source]({REPO}): MIT licensed model, browser port, and verification harness

## Caveats

Revenue assumptions are judgement, not data - there is no public comparable. Tax treatment is
directional and depends on facts a Hawaii CPA must confirm. This is a model, not advice.
""")
    print(f"  {'seo':<18} robots.txt, sitemap.xml, llms.txt, .nojekyll, 3 OG images")


if __name__ == "__main__":
    main()
