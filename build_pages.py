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
  /* Generated pages. Tokens, labels, header, nav, buttons and footer come from
     /assets/vp.css, shared with the app. The frame matches the app's width so
     the header does not jump when you move between them; the reading column
     inside it stays narrow and left-aligned, like the app's own text. */
  .page{max-width:1240px;margin:0 auto;padding:0 var(--gutter) var(--s-8);}
  .page > :not(.site-header):not(.site-footer){max-width:48rem;}

  .crumb{margin:var(--s-7) 0 var(--s-4);}
  .crumb a{color:inherit;text-decoration:none;}
  .crumb a:hover{color:var(--ink);}
  h1{
    font-family:var(--display);font-weight:800;text-transform:uppercase;
    font-size:clamp(2rem,1.3rem + 3vw,3.5rem);line-height:.98;letter-spacing:var(--tr-display);
    margin:0 0 var(--s-5);text-wrap:balance;
  }
  .lede{font-size:var(--fs-lg);line-height:1.65;color:var(--ink-soft);max-width:62ch;margin:0 0 var(--s-6);}
  .meta-row{
    display:flex;flex-wrap:wrap;gap:var(--s-2) var(--s-5);padding:var(--s-3) 0;margin-bottom:var(--s-7);
    border-top:var(--rule);border-bottom:var(--rule);
  }
  .meta-line{color:var(--ink-faint);font-size:var(--fs-sm);margin:calc(-1 * var(--s-2)) 0 var(--s-6);}

  /* ---------- a deck, read as a list of index cards ---------- */
  .card{
    background:var(--surface);border:1px solid var(--line);border-radius:var(--r-2);
    padding:0 var(--s-6) var(--s-6);margin-bottom:var(--s-5);box-shadow:var(--shadow-card);
  }
  .card-n{
    display:flex;align-items:center;gap:var(--s-2);
    margin:0 calc(-1 * var(--s-6)) var(--s-5);padding:var(--s-3) var(--s-6);border-bottom:var(--rule);
    color:var(--ink-soft);
  }
  .card-n::before{content:'';width:6px;height:6px;background:var(--accent);flex:0 0 auto;}
  .card h2{
    font-family:var(--display);font-weight:600;font-size:var(--fs-xl);line-height:1.3;
    letter-spacing:var(--tr-heading);margin:0 0 var(--s-5);color:var(--ink);text-wrap:pretty;
  }
  .takeaway{
    font-family:var(--display);font-weight:600;font-size:var(--fs-lg);line-height:1.4;color:var(--ink);
    padding-left:var(--s-4);border-left:2px solid var(--accent);margin:0 0 var(--s-4);
  }
  .answer{font-size:var(--fs-md);line-height:1.65;color:var(--ink-soft);margin:0;}
  .diagram{margin:0 0 var(--s-5);}
  .diagram svg{display:block;width:100%;height:auto;}
  .opts{list-style:none;margin:0 0 var(--s-5);padding:0;display:flex;flex-direction:column;gap:var(--s-2);}
  .opt{
    display:flex;align-items:flex-start;gap:var(--s-3);padding:var(--s-3) var(--s-4);
    border:1px solid var(--line-soft);border-radius:var(--r-1);font-size:var(--fs-sm);line-height:1.45;color:var(--ink-soft);
  }
  .opt-k{
    flex:0 0 auto;display:grid;place-items:center;width:1.5rem;height:1.5rem;
    border:1px solid var(--line);border-radius:var(--r-1);font-size:.6875rem;font-weight:700;color:var(--ink-faint);
  }
  .opt.is-right{border-color:var(--green);color:var(--ink);}
  .opt.is-right .opt-k{border-color:var(--green);background:var(--green);color:var(--contrast);}

  /* ---------- deck lists: the same table of contents as the app ---------- */
  h2.track{font-size:var(--fs-lg);margin:var(--s-7) 0 0;padding-bottom:var(--s-3);}
  .deck-list{list-style:none;margin:0 0 var(--s-7);padding:0;counter-reset:deck;}
  .deck-item{
    position:relative;counter-increment:deck;
    display:grid;grid-template-columns:3rem minmax(0,1fr) auto;column-gap:var(--s-5);row-gap:var(--s-1);
    padding:var(--s-4) 0;border-bottom:var(--rule);text-decoration:none;color:inherit;
  }
  .deck-item:first-child{border-top:var(--rule-strong);}
  .deck-item::before{
    content:counter(deck,decimal-leading-zero);grid-column:1;grid-row:1 / span 3;padding-top:.15rem;
    font-family:var(--display);font-weight:700;font-size:var(--fs-sm);font-variant-numeric:tabular-nums;color:var(--accent);
  }
  .deck-item .deck-tag{display:none;}
  .deck-item .deck-level{grid-column:2;margin-bottom:var(--s-1);}
  .deck-name{
    grid-column:2;font-family:var(--display);font-weight:700;font-size:1.1875rem;line-height:1.3;
    letter-spacing:-.01em;color:var(--ink);transition:color var(--t-fast);
  }
  .deck-desc{grid-column:2;font-size:var(--fs-sm);color:var(--ink-soft);line-height:1.5;}
  .deck-count{grid-column:3;grid-row:1;padding-top:.3rem;white-space:nowrap;}
  .deck-item:hover .deck-name{color:var(--link);}
  .deck-item:focus-visible{outline:2px solid var(--focus);outline-offset:2px;}

  /* ---------- glossary ---------- */
  .gl-tools{display:flex;flex-wrap:wrap;gap:var(--s-3) var(--s-4);align-items:center;margin:var(--s-6) 0 var(--s-3);}
  .gl-search{
    flex:1 1 16rem;min-width:13rem;min-height:var(--control-h);padding:0 var(--s-4);
    font-family:var(--body);font-size:var(--fs-md);color:var(--ink);
    background:var(--surface);border:1px solid var(--line);border-radius:var(--r-1);
  }
  .gl-search::placeholder{color:var(--ink-faint);}
  .gl-search:focus{outline:2px solid var(--focus);outline-offset:1px;border-color:var(--focus);}
  /* The A-Z index as one strip of cells rather than a scatter of chips. */
  .page > .gl-az{max-width:none;}
  .gl-az{display:flex;flex-wrap:wrap;margin:var(--s-4) 0 var(--s-6);padding:1px 0 0 1px;}
  .gl-az a{
    display:grid;place-items:center;min-width:2.25rem;height:2.25rem;margin:-1px 0 0 -1px;
    font-family:var(--display);font-size:.8125rem;font-weight:700;color:var(--ink-soft);text-decoration:none;
    border:var(--rule);transition:color var(--t-fast),background-color var(--t-fast);
  }
  .gl-az a:hover{color:var(--ink);background:var(--surface);}
  .gl-letter{font-size:var(--fs-xl);line-height:1;margin:var(--s-7) 0 var(--s-2);}
  .gl-item{border-top:var(--rule);padding:var(--s-4) 0;}
  .gl-term{font-family:var(--display);font-weight:700;font-size:var(--fs-lg);letter-spacing:var(--tr-heading);margin:0 0 var(--s-1);}
  .gl-def{font-size:var(--fs-md);line-height:1.6;color:var(--ink);margin:0 0 var(--s-2);}
  .gl-src{font-size:var(--fs-xs);color:var(--ink-faint);}
  .gl-src a{color:var(--link);text-decoration:none;}
  .gl-src a:hover{text-decoration:underline;text-underline-offset:3px;}
  .gl-empty{color:var(--ink-faint);font-size:var(--fs-md);padding:var(--s-5) 0;}

  /* ---------- prose pages ---------- */
  .prose{font-size:var(--fs-md);}
  .prose h2{
    font-family:var(--display);font-weight:700;font-size:var(--fs-lg);letter-spacing:var(--tr-heading);
    margin:var(--s-7) 0 var(--s-3);padding-top:var(--s-4);border-top:var(--rule);
  }
  .prose p{margin:0 0 var(--s-4);line-height:1.75;max-width:66ch;}
  .prose ul{margin:0 0 var(--s-5);padding-left:1.15rem;max-width:66ch;}
  .prose li{margin:0 0 var(--s-2);line-height:1.7;}
  .prose a{color:var(--link);text-underline-offset:3px;}
  .prose a.btn{color:var(--contrast);}   /* .prose a would otherwise tint the button label */

  /* calls to action are ruled bands, not boxes */
  .cta-band,.cta-block{
    display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:var(--s-4) var(--s-5);
    margin:var(--s-7) 0;padding:var(--s-5) 0;border-top:var(--rule-strong);border-bottom:var(--rule);text-align:left;
  }
  .cta-band p,.cta-block p{margin:0;flex:1 1 20rem;color:var(--ink-soft);font-size:var(--fs-md);}

  @media (max-width:640px){
    .lede{font-size:var(--fs-md);}
    .card{padding:0 var(--s-5) var(--s-5);}
    .card-n{margin:0 calc(-1 * var(--s-5)) var(--s-4);padding:var(--s-3) var(--s-5);}
    .deck-item{grid-template-columns:2rem minmax(0,1fr);column-gap:var(--s-3);}
    .deck-count{grid-column:2;grid-row:auto;padding-top:var(--s-1);}
    .cta-band .btn,.cta-block .btn{width:100%;}
  }
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Archivo:wght@400;600;700;800&display=swap">')

# The shared design system. It is inlined into every page rather than linked, so
# a page can never load without it (a missing /assets folder once left the whole
# site unstyled).
VP_CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "vp.css"),
              encoding="utf-8").read()
VP_BEGIN = "/* vp.css:begin - copied from assets/vp.css by build_pages.py; edit that file and rebuild */"
VP_END = "/* vp.css:end */"


def sync_app_css(path="index.html"):
    """Refresh the copy of assets/vp.css inside index.html. Only the text between
    the two markers changes; the app's own styles and scripts are left alone."""
    s = open(path, encoding="utf-8").read()
    a, b = s.index(VP_BEGIN), s.index(VP_END)
    assert s.count(VP_BEGIN) == 1 and s.count(VP_END) == 1 and a < b
    new = s[:a] + VP_BEGIN + "\n" + VP_CSS + s[b:]
    if new != s:
        open(path, "w", encoding="utf-8").write(new)


def level_tag(deck):
    """The difficulty marker, styled by .deck-level in assets/vp.css."""
    lv = deck.get("level")
    return f'<span class="deck-level" data-level="{esc(lv)}">{esc(lv.capitalize())}</span>' if lv else ''


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
<script>(function(){{try{{var s=localStorage.getItem('vp-theme');
var d=s?s==='dark':window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;
if(d){{document.documentElement.setAttribute('data-theme','dark');}}}}catch(e){{}}}})();</script>
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
<style>{VP_CSS}{STYLE}</style>
</head>
<body>
<div class="page">
  <header class="site-header">
    <a class="wordmark" href="{SITE}/" aria-label="ViewPrep home"><svg class="wordmark-mark" width="26" height="26" viewBox="0 0 64 64" aria-hidden="true"><rect class="wm-sq" width="64" height="64" rx="13"/><path d="M14 13 L22.5 13 L32 38 L41.5 13 L50 13 L36.5 52 L27.5 52 Z" fill="#2C4E92"/></svg><span class="wordmark-text"><span class="wordmark-primary">View</span><span class="wordmark-secondary">Prep</span></span></a>
    <nav class="main-nav" aria-label="Sections">
      <a class="nav-item{' is-active' if section == 'cards' else ''}" href="{SITE}/#track-ib">Investment Banking</a>
      <a class="nav-item" href="{SITE}/#track-consulting">Consulting</a>
      <a class="nav-item{' is-active' if section == 'glossary' else ''}" href="{SITE}/glossary.html">Glossary</a>
      <a class="nav-item" href="{SITE}/#test">Test yourself</a>
    </nav>
    <nav class="header-nav">
      <button class="theme-btn" id="theme-btn" type="button" aria-pressed="false"
              title="Switch between light and dark" aria-label="Switch between light and dark">
        <svg class="ic-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/>
          <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
        <svg class="ic-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/></svg>
      </button>
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
<script>
(function(){{
  var btn=document.getElementById('theme-btn');
  var meta=document.querySelector('meta[name="theme-color"]');
  function paint(){{
    var d=document.documentElement.getAttribute('data-theme')==='dark';
    if(btn){{btn.setAttribute('aria-pressed',String(d));}}
    if(meta){{meta.setAttribute('content', d?'#0E1117':'#F2F1EC');}}
  }}
  paint();
  if(btn){{btn.addEventListener('click',function(){{
    var d=document.documentElement.getAttribute('data-theme')==='dark';
    if(d){{document.documentElement.removeAttribute('data-theme');}}
    else{{document.documentElement.setAttribute('data-theme','dark');}}
    try{{localStorage.setItem('vp-theme', d?'light':'dark');}}catch(e){{}}
    paint();
  }});}}
}})();
</script>
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
               f'{level_tag(deck)}'
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
                f'{level_tag(s)}'
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
                f'{level_tag(d)}'
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

    # Older builds wrote each deck page to the site root as well. Those copies are
    # still served (viewprep.net/accounting.html), so keep them identical to
    # decks/ rather than letting them serve stale text.
    for d in decks:
        root_copy = f"{d['id']}.html"
        if os.path.exists(root_copy):
            open(root_copy, "w", encoding="utf-8").write(deck_page(d, decks))
            written.append(root_copy)

    sync_app_css()

    total_cards = sum(len(d["cards"]) for d in decks)
    total_kb = sum(os.path.getsize(p) for p in written) / 1024
    print(f"{len(written)} files, {total_cards} cards, {total_kb:.0f} KB total")


if __name__ == "__main__":
    main()
