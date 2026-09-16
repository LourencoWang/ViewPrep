#!/usr/bin/env python3
"""
Generate crawlable static pages for ViewPrep from decks.json.

Why this exists: the site is a single page that loads all 400 cards from JSON with
JavaScript. Google therefore indexes one page instead of 400, and AI answer engines
(GPTBot, ClaudeBot, PerplexityBot) see nothing at all, because they read raw HTML and
do not run JavaScript. These pages put the same content in plain HTML.

They are not doorway pages: each one is a genuinely readable reference version of a
deck, linked both ways with the interactive study tool.

Run from the repo root:   python3 build_pages.py
Re-run after any decks.json change.
"""

import json
import re
import legal_pages
import os
import html
import datetime

SITE = "https://viewprep.net"
OUT_DIR = "decks"

TRACK_NAME = {"ib": "Investment banking", "consulting": "Consulting"}


def esc(s):
    return html.escape(str(s), quote=True)


# --- shared chrome -----------------------------------------------------------------

STYLE = """
  :root{
    --bg:#F4F6FA; --ink:#0C0C0D; --ink-soft:#54545A; --ink-faint:#8A8A90;
    --line:rgba(12,12,13,0.20); --line-soft:rgba(28,36,60,0.10);
    --surface:#FFFFFF; --surface-strong:#FFFFFF;
    --blue:#2F5FE0; --amber:#2C4E92; --amber-ink:#2C4E92; --green:#1D8A57; --red:#C63A2C;
    --contrast:#FFFFFF;
    --display:'Archivo',-apple-system,'Segoe UI',sans-serif;
    --body:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  }
  *,*::before,*::after{box-sizing:border-box;}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);
       line-height:1.6;-webkit-font-smoothing:antialiased;}
  a{color:inherit;}
  .page{max-width:820px;margin:0 auto;padding:0 1.5rem 5rem;}
  .site-header{display:flex;justify-content:space-between;align-items:center;gap:1rem;
    padding:1.75rem 0;border-bottom:1px solid var(--line-soft);}
  .wordmark{font-family:var(--display);font-size:1.05rem;letter-spacing:.03em;
    text-decoration:none;}
  .wordmark b{font-weight:800;color:var(--ink);}
  .wordmark span{font-weight:400;color:var(--ink-faint);}
  .header-cta{font-family:var(--body);font-size:.72rem;font-weight:700;letter-spacing:.06em;
    text-transform:uppercase;color:var(--ink-soft);text-decoration:none;
    border:1px solid var(--line-soft);border-radius:999px;padding:.5rem 1rem;}
  .header-cta:hover{border-color:var(--blue);color:var(--ink);}
  .crumb{font-family:var(--body);font-size:.72rem;font-weight:600;letter-spacing:.07em;
    text-transform:uppercase;color:var(--ink-faint);margin:2rem 0 .9rem;}
  .crumb a{color:var(--ink-faint);text-decoration:none;}
  .crumb a:hover{color:var(--blue);}
  h1{font-family:var(--display);font-weight:700;text-transform:uppercase;
    font-size:clamp(1.9rem,5vw,2.9rem);line-height:1.02;letter-spacing:-.012em;
    margin:0 0 1rem;text-wrap:balance;}
  .lede{color:var(--ink-soft);font-size:1rem;line-height:1.65;max-width:60ch;margin:0 0 1.5rem;}
  .meta-row{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;padding:1rem 0;
    border-top:1px solid var(--line-soft);border-bottom:1px solid var(--line-soft);
    font-size:.72rem;font-weight:600;letter-spacing:.07em;text-transform:uppercase;
    color:var(--ink-faint);font-variant-numeric:tabular-nums;margin-bottom:2.25rem;}
  .btn{display:inline-flex;align-items:center;gap:.5rem;padding:.85rem 1.6rem;
    border-radius:999px;background:var(--ink);color:var(--contrast);text-decoration:none;
    font-family:var(--display);font-size:.8rem;font-weight:700;letter-spacing:.06em;
    text-transform:uppercase;}
  .btn:hover{background:#2A2A2E;}
  .card{border:1px solid var(--line-soft);border-radius:16px;background:var(--surface);
    padding:1.5rem 1.6rem;margin-bottom:1rem;}
  .card-n{font-family:var(--body);font-size:.66rem;font-weight:700;letter-spacing:.1em;
    text-transform:uppercase;color:var(--blue);margin-bottom:.7rem;}
  .card h2{font-family:var(--display);font-weight:600;font-size:1.12rem;line-height:1.42;
    letter-spacing:-.005em;margin:0 0 1rem;color:var(--ink);}
  .takeaway{font-family:var(--display);font-weight:700;font-size:1rem;line-height:1.45;
    color:var(--ink);margin:0 0 .7rem;}
  .answer{font-size:.95rem;line-height:1.65;color:var(--ink-soft);margin:0;}
  .opts{list-style:none;margin:0 0 1rem;padding:0;display:flex;flex-direction:column;gap:.45rem;}
  .opt{display:flex;align-items:flex-start;gap:.7rem;border:1px solid var(--line-soft);
    border-radius:12px;padding:.6rem .8rem;font-size:.92rem;line-height:1.45;color:var(--ink-soft);}
  .opt-k{flex:0 0 auto;width:1.3rem;height:1.3rem;border-radius:50%;border:1px solid var(--line-soft);
    display:flex;align-items:center;justify-content:center;font-size:.68rem;font-weight:700;
    color:var(--ink-faint);}
  .opt.is-right{border-color:var(--green);color:var(--ink);}
  .opt.is-right .opt-k{border-color:var(--green);background:var(--green);color:#fff;}
  .diagram{margin:0 0 1.1rem;}
  .diagram svg{display:block;width:100%;height:auto;}
  .deck-list{display:grid;grid-template-columns:repeat(2,1fr);gap:1rem;margin-bottom:2.5rem;}
  .deck-item{border:1px solid var(--line-soft);border-radius:16px;background:var(--surface);
    padding:1.3rem 1.4rem;text-decoration:none;display:flex;flex-direction:column;gap:.5rem;}
  .deck-item:hover{border-color:var(--blue);}
  .deck-tag{font-size:.66rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
    color:var(--blue);}
  .deck-name{font-family:var(--display);font-weight:700;font-size:1rem;
    text-transform:uppercase;letter-spacing:.01em;color:var(--ink);}
  .deck-desc{font-size:.88rem;color:var(--ink-soft);line-height:1.5;}
  .deck-count{font-size:.7rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
    color:var(--ink-faint);margin-top:auto;padding-top:.3rem;}
  h2.track{font-family:var(--display);font-weight:700;font-size:1.2rem;
    text-transform:uppercase;letter-spacing:.04em;margin:2.5rem 0 1.2rem;
    border-left:5px solid var(--amber);padding-left:.6rem;}
  .site-header{flex-wrap:wrap;}
  .main-nav{display:flex;align-items:center;justify-content:center;gap:.35rem;
    flex:1 1 auto;flex-wrap:wrap;}
  .nav-item{font-family:var(--body);font-size:.76rem;font-weight:700;letter-spacing:.04em;
    text-transform:uppercase;color:var(--ink-soft);text-decoration:none;white-space:nowrap;
    padding:.5rem .95rem;border-radius:999px;border:1px solid transparent;
    transition:color .15s ease,border-color .15s ease,background .15s ease;}
  .nav-item:hover{color:var(--ink);border-color:var(--line-soft);}
  .nav-item.is-active{color:var(--ink);border-color:var(--line);background:var(--surface);}
  .header-nav{display:flex;align-items:center;gap:1.1rem;}
  @media (max-width:860px){
    .site-header{row-gap:.65rem;}
    .main-nav{order:3;flex:1 0 100%;justify-content:center;flex-wrap:nowrap;}
    .nav-item{font-size:.7rem;padding:.45rem .8rem;}
  }
  @media (max-width:600px){
    .nav-item{padding:.45rem .7rem;font-size:.66rem;}
    .main-nav{gap:.25rem;}
  }
  .gl-tools{display:flex;flex-wrap:wrap;gap:.8rem;align-items:center;margin:1.6rem 0 .4rem;}
  .gl-search{flex:1 1 260px;min-width:220px;font-family:var(--body);font-size:.95rem;
    padding:.7rem .95rem;border:1px solid var(--line);border-radius:12px;
    background:var(--surface);color:var(--ink);}
  .gl-search::placeholder{color:var(--ink-faint);}
  .gl-count{font-size:.75rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
    color:var(--ink-faint);}
  .gl-az{display:flex;flex-wrap:wrap;gap:.35rem;margin:.9rem 0 2rem;}
  .gl-az a{font-family:var(--display);font-size:.78rem;font-weight:700;color:var(--ink-soft);
    text-decoration:none;padding:.35rem .6rem;border:1px solid var(--line-soft);border-radius:8px;}
  .gl-az a:hover{color:var(--ink);border-color:var(--line);}
  .gl-letter{font-family:var(--display);font-weight:700;font-size:1.1rem;
    border-left:5px solid var(--amber);padding-left:.6rem;margin:2.2rem 0 .9rem;}
  .gl-item{border-top:1px solid var(--line-soft);padding:1.1rem 0;}
  .gl-term{font-family:var(--display);font-weight:700;font-size:1.05rem;margin:0 0 .35rem;}
  .gl-def{font-size:.95rem;line-height:1.6;color:var(--ink);margin:0 0 .5rem;}
  .gl-src{font-size:.78rem;color:var(--ink-faint);}
  .gl-src a{color:var(--blue);text-decoration:none;}
  .gl-src a:hover{text-decoration:underline;}
  .gl-empty{color:var(--ink-faint);font-size:.95rem;padding:1.5rem 0;}
  .cta-band{border:1px solid var(--line-soft);border-radius:16px;background:var(--surface);
    padding:1.6rem;margin:2.5rem 0;text-align:center;}
  .cta-band p{margin:0 0 1.1rem;color:var(--ink-soft);font-size:.95rem;}
  .meta-line{color:var(--ink-faint);font-size:.9rem;margin:-.4rem 0 2rem;}
  .prose h2{font-size:1.15rem;margin:2.2rem 0 .7rem;letter-spacing:-.01em;}
  .prose p{margin:0 0 1rem;line-height:1.75;}
  .prose ul{margin:0 0 1.2rem;padding-left:1.15rem;}
  .prose li{margin:0 0 .55rem;line-height:1.7;}
  .prose a{color:var(--blue);}
  /* .prose a would otherwise beat .btn on specificity and tint the button text. */
  .prose a.btn{color:var(--contrast);}
  .cta-block{margin-top:3rem;padding-top:2rem;border-top:1px solid var(--line-soft);}
  .site-footer{border-top:1px solid var(--line-soft);padding:1.5rem 0 0;margin-top:3rem;
    color:var(--ink-faint);font-size:.82rem;line-height:1.6;}
  .site-footer a{color:var(--ink-soft);}
  @media (max-width:600px){
    .page{padding:0 1.15rem 3rem;}
    .deck-list{grid-template-columns:1fr;}
    .card{padding:1.2rem 1.2rem;}
  }
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Archivo:wght@400;500;600;700;800&display=swap">')


def head(title, desc, canonical, deck_id=None, section="cards"):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#F2F1EC">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/appletouchicon.png">
<meta property="og:type" content="article">
<meta property="og:site_name" content="ViewPrep">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/ogimage.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE}/ogimage.png">
{FONTS}
<style>{STYLE}</style>
</head>
<body>
<div class="page">
  <header class="site-header">
    <a class="wordmark" href="{SITE}/"><b>View</b><span>Prep</span></a>
    <nav class="main-nav" aria-label="Sections">
      <a class="nav-item{' is-active' if section == 'cards' else ''}" href="{SITE}/#track-ib">Investment Banking</a>
      <a class="nav-item" href="{SITE}/#track-consulting">Consulting</a>
      <a class="nav-item{' is-active' if section == 'glossary' else ''}" href="{SITE}/glossary.html">Glossary</a>
      <a class="nav-item" href="{SITE}/#test">Test yourself</a>
    </nav>
    <nav class="header-nav">
      <a class="header-cta" href="{SITE}/{('?deck=' + deck_id) if deck_id else ''}">Study these cards</a>
    </nav>
  </header>
"""


def footer(deck_id=None):
    return f"""
  <footer class="site-footer">
    <p>ViewPrep is an independent study resource. It is not affiliated with, endorsed
    by, or sourced from any university, employer, or prep platform.</p>
    <p><a href="{SITE}/{('?deck=' + deck_id) if deck_id else ''}">Study these cards interactively</a> &middot;
       <a href="{SITE}/decks/">All decks</a> &middot;
       <a href="{SITE}/glossary.html">Glossary</a> &middot;
       <a href="{SITE}/commercial-awareness.html">Commercial awareness</a> &middot;
       <a href="{SITE}/faq.html">FAQ</a> &middot;
       <a href="{SITE}/privacy.html">Privacy</a> &middot;
       <a href="{SITE}/terms.html">Terms</a></p>
  </footer>
</div>
</body>
</html>
"""


def deck_page(deck, all_decks):
    cards = deck["cards"]
    title = f"{deck['name']} flashcards | ViewPrep"
    desc = f"{deck['description']} {len(cards)} free flashcards with answers, written for people with no finance background."
    canonical = f"{SITE}/{OUT_DIR}/{deck['id']}.html"

    out = [head(title, desc, canonical, deck["id"])]
    out.append(f'  <p class="crumb"><a href="{SITE}/">ViewPrep</a> / '
               f'<a href="{SITE}/{OUT_DIR}/">Decks</a> / {esc(TRACK_NAME[deck["track"]])}</p>')
    out.append(f"  <h1>{esc(deck['name'])}</h1>")
    out.append(f'  <p class="lede">{esc(deck["intro"])}</p>')
    out.append('  <div class="meta-row">'
               f'<span>{len(cards)} cards</span>'
               f'<span>{esc(TRACK_NAME[deck["track"]])}</span>'
               '<span>Free, no signup</span></div>')

    for i, c in enumerate(cards):
        out.append('  <article class="card">')
        out.append(f'    <div class="card-n">Card {i + 1} of {len(cards)}</div>')
        out.append(f'    <h2>{esc(c["q"])}</h2>')
        if c.get("choices"):
            # Multiple-choice card: the static page marks the right option, since
            # there is nothing to click on a page that has to work for a crawler.
            out.append('    <ul class="opts">')
            for k, ch in enumerate(c["choices"]):
                cls = " is-right" if k == c.get("answer") else ""
                out.append(f'      <li class="opt{cls}"><span class="opt-k">{"ABCD"[k]}</span>'
                           f'<span>{esc(ch)}</span></li>')
            out.append("    </ul>")
        if c.get("image"):
            # Deck-authored inline SVG, not user input, so it is inserted as markup.
            out.append(f'    <div class="diagram">{c["image"]}</div>')
        if c.get("takeaway"):
            out.append(f'    <p class="takeaway">{esc(c["takeaway"])}</p>')
        out.append(f'    <p class="answer">{esc(c["a"])}</p>')
        out.append('  </article>')

    out.append('  <div class="cta-band">')
    out.append('    <p>Reading is not the same as remembering. Study this deck with '
               'scheduled review so the cards come back before you forget them.</p>')
    out.append(f'    <a class="btn" href="{SITE}/?deck={deck["id"]}">Study {esc(deck["name"])}</a>')
    out.append('  </div>')

    # Sibling decks in the same track give crawlers a path between pages.
    sibs = [d for d in all_decks if d["track"] == deck["track"] and d["id"] != deck["id"]]
    if sibs:
        out.append(f'  <h2 class="track">More {esc(TRACK_NAME[deck["track"]].lower())} decks</h2>')
        out.append('  <div class="deck-list">')
        for s in sibs:
            out.append(
                f'    <a class="deck-item" href="{SITE}/{OUT_DIR}/{s["id"]}.html">'
                f'<span class="deck-tag">{esc(s["tag"])}</span>'
                f'<span class="deck-name">{esc(s["name"])}</span>'
                f'<span class="deck-desc">{esc(s["description"])}</span>'
                f'<span class="deck-count">{len(s["cards"])} cards</span></a>')
        out.append('  </div>')

    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": c["q"],
             "acceptedAnswer": {"@type": "Answer",
                                "text": (c.get("takeaway", "") + " " + c["a"]).strip()}}
            for c in cards
        ],
    }
    out.append('  <script type="application/ld+json">'
               + json.dumps(faq, ensure_ascii=False) + '</script>')
    out.append(footer(deck["id"]))
    return "\n".join(out)


def hub_page(decks):
    total = sum(len(d["cards"]) for d in decks)
    title = "All flashcard decks | ViewPrep"
    desc = (f"All {total} ViewPrep flashcards across {len(decks)} decks covering investment "
            "banking and consulting interviews. Free, with full answers.")
    canonical = f"{SITE}/{OUT_DIR}/"

    out = [head(title, desc, canonical)]
    out.append(f'  <p class="crumb"><a href="{SITE}/">ViewPrep</a> / Decks</p>')
    out.append("  <h1>Every deck</h1>")
    out.append(f'  <p class="lede">All {total} cards, ordered so each '
               'deck starts with the plainest concepts and builds toward the harder, multi-step '
               'questions interviewers use to separate candidates. Every card below shows its '
               'full answer.</p>')
    out.append('  <div class="meta-row">'
               f'<span>{total} cards</span><span>{len(decks)} decks</span>'
               '<span>Free, no signup</span></div>')

    for track in ("ib", "consulting"):
        ds = [d for d in decks if d["track"] == track]
        out.append(f'  <h2 class="track">{esc(TRACK_NAME[track])} &middot; {len(ds)} decks</h2>')
        out.append('  <div class="deck-list">')
        for d in ds:
            out.append(
                f'    <a class="deck-item" href="{SITE}/{OUT_DIR}/{d["id"]}.html">'
                f'<span class="deck-tag">{esc(d["tag"])}</span>'
                f'<span class="deck-name">{esc(d["name"])}</span>'
                f'<span class="deck-desc">{esc(d["description"])}</span>'
                f'<span class="deck-count">{len(d["cards"])} cards</span></a>')
        out.append('  </div>')

    out.append('  <div class="cta-band">')
    out.append('    <p>Pick a deck and study it with scheduled review, so cards come back '
               'just before you would have forgotten them.</p>')
    out.append(f'    <a class="btn" href="{SITE}/">Start studying</a>')
    out.append('  </div>')
    out.append(footer())
    return "\n".join(out)


def simple_page(slug, title, desc, body, jsonld=None):
    """A standalone prose page (privacy, terms, FAQ). Uses the same head() and
    footer() as every deck page so these cannot drift out of style."""
    canonical = f"{SITE}/{slug}"
    out = [head(title, desc, canonical)]
    out.append('  <div class="prose">')
    out.append(body)
    out.append("  </div>")
    if jsonld is not None:
        out.append('  <script type="application/ld+json">'
                   + json.dumps(jsonld, ensure_ascii=False) + "</script>")
    out.append(footer())
    return "\n".join(out)


def sitemap(decks):
    today = datetime.date.today().isoformat()
    urls = [(f"{SITE}/", "1.0"), (f"{SITE}/{OUT_DIR}/", "0.9"),
            (f"{SITE}/glossary.html", "0.8")]
    urls += [(f"{SITE}/{OUT_DIR}/{d['id']}.html", "0.8") for d in decks]
    # A 404 page carries priority None so it is generated but kept out of the sitemap.
    urls += [(f"{SITE}/{slug}", pri)
             for slug, _t, _d, _b, _j, pri in legal_pages.PAGES if pri]
    body = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{today}</lastmod>\n"
        f"    <priority>{p}</priority>\n  </url>" for u, p in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{body}\n</urlset>\n")


ROBOTS = f"""# ViewPrep

User-agent: *
Allow: /

# Answer engines are welcome to read and cite these cards.
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: {SITE}/sitemap.xml
"""



# ---------------------------------------------------------------- glossary ---
# Terms are derived from the decks themselves, never written by hand: a card
# only becomes an entry when its own takeaway opens by naming the term. That
# keeps every definition traceable to a real card and stops the glossary
# drifting away from what the site actually teaches.

_BAD_END = {"when","before","after","minus","plus","the","a","an","and","or","of","for","to",
            "it","is","are","that","which","on","in","with","by","from","than","you","your"}
_GENERIC = {"company","books","grid","case","thing","business","money","number","people","work"}
_VERB_START = {"build","buy","use","keep","start","make","take","pick","run","ask","say","tell",
               "show","add","put","find","know","learn","name","answer","check","write","treat"}


def _clean_term(t):
    t = t.strip().strip(".,;:")
    t = re.sub(r"^(?:an?|the)\s+", "", t, flags=re.I)
    w = t.split()
    if not w or len(w) > 4 or len(t) < 3: return None
    if w[0].lower() in _VERB_START: return None
    if w[-1].lower() in _BAD_END: return None
    if t.lower() in _GENERIC: return None
    return t


def _defines(term, definition):
    head = definition[:70].lower()
    return term.lower().rstrip("s") in head or term.lower() in head


def glossary_terms(decks):
    out = {}
    for d in decks:
        for c in d["cards"]:
            tk = c["takeaway"].strip()
            cands = [_clean_term(q) for q in re.findall(r'[\u201c"]([^\u201d"]{2,45})[\u201d"]', c["q"])]
            m = re.match(r"^(?:The |A |An )?([A-Za-z][A-Za-z0-9 \-/&'\u2019]{2,45}?)\s+(?:is|are|means|refers to)\s", tk)
            if m:
                cands.append(_clean_term(m.group(1)))
            for t in dict.fromkeys([x for x in cands if x]):
                if not _defines(t, tk): continue
                k = t.lower()
                if k in out: continue
                out[k] = {"term": t, "deck": d["id"], "deck_name": d["name"],
                          "track": d["track"], "definition": tk}
    return out


def _slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def glossary_page(decks):
    terms = glossary_terms(decks)
    keys = sorted(terms, key=lambda k: terms[k]["term"].lower())
    letters = sorted({terms[k]["term"][0].upper() for k in keys})

    title = "Finance glossary | ViewPrep"
    desc = (f"{len(terms)} finance and consulting terms explained in one line each, "
            "from accounting basics to case structuring. Free, no account.")
    canonical = f"{SITE}/glossary.html"

    out = [head(title, desc, canonical, section="glossary")]
    out.append(f'  <p class="crumb"><a href="{SITE}/">ViewPrep</a> / Glossary</p>')
    out.append("  <h1>Finance glossary</h1>")
    out.append(f'  <p class="lede">{len(terms)} terms, each explained in a single sentence and '
               "linked to the deck where it is taught properly. Every definition is taken from "
               "a card on this site, so nothing here is longer than it needs to be.</p>")
    out.append('  <div class="gl-tools">'
               '<input class="gl-search" id="gl-search" type="search" '
               'placeholder="Search a term, e.g. EBITDA" aria-label="Search the glossary">'
               f'<span class="gl-count" id="gl-count">{len(terms)} terms</span></div>')
    out.append('  <div class="gl-az">' + "".join(
        f'<a href="#letter-{L}">{L}</a>' for L in letters) + "</div>")

    cur = None
    for k in keys:
        e = terms[k]
        L = e["term"][0].upper()
        if L != cur:
            cur = L
            out.append(f'  <h2 class="gl-letter" id="letter-{L}">{L}</h2>')
        sl = _slug(e["term"])
        out.append(f'  <div class="gl-item" id="{sl}" data-term="{esc(e["term"].lower())} '
                   f'{esc(e["definition"].lower())}">')
        out.append(f'    <h3 class="gl-term">{esc(e["term"])}</h3>')
        out.append(f'    <p class="gl-def">{esc(e["definition"])}</p>')
        out.append(f'    <p class="gl-src">Taught in '
                   f'<a href="{SITE}/{OUT_DIR}/{e["deck"]}.html">{esc(e["deck_name"])}</a> '
                   f'&middot; <a href="{SITE}/?deck={e["deck"]}">study this deck</a></p>')
        out.append("  </div>")
    out.append('  <p class="gl-empty" id="gl-empty" hidden>No term matches that. '
               'Try a shorter word.</p>')

    out.append("""  <script>
  (function(){
    var box = document.getElementById('gl-search');
    var items = [].slice.call(document.querySelectorAll('.gl-item'));
    var heads = [].slice.call(document.querySelectorAll('.gl-letter'));
    var count = document.getElementById('gl-count');
    var empty = document.getElementById('gl-empty');
    if (!box) { return; }
    box.addEventListener('input', function(){
      var q = box.value.trim().toLowerCase();
      var shown = 0;
      items.forEach(function(el){
        var hit = !q || el.getAttribute('data-term').indexOf(q) !== -1;
        el.hidden = !hit;
        if (hit) { shown++; }
      });
      // hide a letter heading when everything under it is filtered out
      heads.forEach(function(h){
        var n = h.nextElementSibling, any = false;
        while (n && !n.classList.contains('gl-letter')) {
          if (n.classList.contains('gl-item') && !n.hidden) { any = true; break; }
          n = n.nextElementSibling;
        }
        h.hidden = !any;
      });
      count.textContent = shown + (shown === 1 ? ' term' : ' terms');
      empty.hidden = shown !== 0;
    });
  })();
  </script>""")
    out.append(footer())
    return "\n".join(out)


def main():
    decks = json.load(open("decks.json", encoding="utf-8"))
    os.makedirs(OUT_DIR, exist_ok=True)

    written = []
    for d in decks:
        path = os.path.join(OUT_DIR, f"{d['id']}.html")
        open(path, "w", encoding="utf-8").write(deck_page(d, decks))
        written.append(path)

    open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8").write(hub_page(decks))
    written.append(os.path.join(OUT_DIR, "index.html"))
    for slug, title, desc, body_fn, jsonld_fn, _pri in legal_pages.PAGES:
        html = simple_page(slug, title, desc, body_fn(),
                           jsonld_fn() if jsonld_fn else None)
        open(slug, "w", encoding="utf-8").write(html)
        written.append(slug)

    open("glossary.html", "w", encoding="utf-8").write(glossary_page(decks))
    written.append("glossary.html")

    open("sitemap.xml", "w", encoding="utf-8").write(sitemap(decks))
    written.append("sitemap.xml")
    open("robots.txt", "w", encoding="utf-8").write(ROBOTS)
    written.append("robots.txt")

    total_cards = sum(len(d["cards"]) for d in decks)
    total_kb = sum(os.path.getsize(p) for p in written) / 1024
    print(f"{len(written)} files, {total_cards} cards, {total_kb:.0f} KB total")


if __name__ == "__main__":
    main()
