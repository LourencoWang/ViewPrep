"""Privacy, Terms and FAQ pages for ViewPrep.

Imported by build_pages.py so these share head(), footer() and STYLE with the
deck pages rather than being hand-written lookalikes that drift apart.

Every factual claim in the privacy page was checked against index.html:
  localStorage keys   flashprep_visitor_id_v1, flashprep_progress_v2
                      (flashprep_progress_v1 is read once to migrate, then ignored)
  Supabase auth       email + password, hashed by Supabase
  progress table      user_id, deck_id, card_index, reps, ef, interval_days,
                      due_at, last_reviewed_at, updated_at
  visits table        visitor_id, timestamp
  events table        visitor_id, user_id (only when signed in), name, props, created_at
  third parties       Supabase, GitHub Pages, Cloudflare, Google Fonts, jsDelivr
"""

import json

LAST_UPDATED = "1 September 2026"
CONTACT = "support@viewprep.net"


def _p(text):
    return f"  <p>{text}</p>"


def _h(text):
    return f"  <h2>{text}</h2>"


def _ul(items):
    return "  <ul>\n" + "\n".join(f"    <li>{i}</li>" for i in items) + "\n  </ul>"


# --------------------------------------------------------------------------- privacy
def privacy_body():
    o = []
    o.append('  <p class="crumb"><a href="/">ViewPrep</a> / Privacy</p>')
    o.append("  <h1>Privacy policy</h1>")
    o.append(f'  <p class="meta-line">Last updated {LAST_UPDATED}</p>')

    o.append(_p("ViewPrep is a free flashcard site run by a single independent operator. "
                "This page describes exactly what the site stores, where it goes, and how to "
                "get rid of it. It describes the site as actually built, not a generic template."))

    o.append(_h("The short version"))
    o.append(_p("You can use the entire site without an account and without giving us anything "
                "identifying. If you create an account, we store your email address so you can "
                "sign back in, and your study progress so it follows you between devices. We do "
                "not run ads, we do not sell data, and there are no advertising or social media "
                "trackers on the site."))

    o.append(_h("What is stored in your browser"))
    o.append(_p("Two items are kept in your browser's local storage. They stay on your device "
                "and are not cookies:"))
    o.append(_ul([
        "<b>flashprep_visitor_id_v1</b> &ndash; a random identifier generated in your browser. "
        "It is not linked to your name or email unless you create an account, and it lets us "
        "count how many separate people use the site rather than how many page loads there were.",
        "<b>flashprep_progress_v2</b> &ndash; which cards you have reviewed and when each is next "
        "due. This is what makes the review scheduling work when you are signed out.",
    ]))
    o.append(_p("Clearing your browser data for this site removes both. If you are signed out, "
                "that erases your progress permanently, because there is no other copy."))

    o.append(_h("What is stored on our server"))
    o.append(_p("The site uses <a href=\"https://supabase.com\" rel=\"noopener\">Supabase</a> as "
                "its database and login provider. Three tables hold data:"))
    o.append(_ul([
        "<b>Accounts</b> &ndash; your email address and a password. Passwords are hashed by "
        "Supabase before storage, which means they are stored as an irreversible scramble. "
        "Nobody, including the site owner, can read your password.",
        "<b>Progress</b> &ndash; for signed-in users only: which deck and card, how many times you "
        "have reviewed it, its current interval, and when it is next due. It is linked to your "
        "account so it can sync across devices.",
        "<b>Usage events</b> &ndash; a small number of anonymous records such as opening a deck, "
        "reviewing your first card of a session, finishing a session, and being shown the account "
        "prompt. Each carries the random browser identifier above, and your account id only if "
        "you are signed in. We record what happened, not what you answered.",
    ]))
    o.append(_p("We do not store your IP address in any of these tables, and we do not store "
                "your name, your university, or anything you did not type into the signup form."))

    o.append(_h("Why we collect it"))
    o.append(_p("The account data exists to give you a login and to sync progress, which is the "
                "service you asked for by signing up. The usage events exist so we can tell which "
                "parts of the site people abandon and fix them; a site nobody can measure is a "
                "site nobody can improve. Under UK and EU data protection law, the first rests on "
                "performing the service you requested and the second on our legitimate interest "
                "in operating and improving the site. If you would rather not be counted at all, "
                "browser storage can be blocked for this site and the tracking silently stops "
                "working, without breaking anything else."))

    o.append(_h("Third parties that see something"))
    o.append(_p("Being honest about this, because these are requests your browser makes when it "
                "loads the page, and each one reveals your IP address to the company involved:"))
    o.append(_ul([
        "<b>GitHub Pages</b> hosts the site's files.",
        "<b>Cloudflare</b> handles the domain and routes traffic.",
        "<b>Supabase</b> stores accounts, progress and events.",
        "<b>Google Fonts</b> serves the typeface the site uses.",
        "<b>jsDelivr</b> serves the Supabase JavaScript library.",
    ]))
    o.append(_p("None of these are advertising networks and none receive your study data. The "
                "last two are ordinary content delivery networks, but they are third parties, so "
                "they are named here rather than left out."))

    o.append(_h("How long it is kept"))
    o.append(_p("Account and progress data is kept until you ask for it to be deleted. Usage "
                "events are kept while they are useful for understanding how the site is used. "
                "Browser storage stays until you clear it."))

    o.append(_h("Your rights"))
    o.append(_p("If you are in the UK or the EU you have the right to see what we hold about you, "
                "correct it, have it deleted, or object to how it is used. In practice, for this "
                "site, the fastest route to all of the above is to email us and ask."))
    o.append(_p(f'Email <a href="mailto:{CONTACT}">{CONTACT}</a> and say what you want done. '
                "Deletion requests remove your account, your synced progress, and any events tied "
                "to your account id."))

    o.append(_h("Children"))
    o.append(_p("The site is intended for university students and adults preparing for job "
                "interviews. It is not directed at children."))

    o.append(_h("Changes"))
    o.append(_p("If this policy changes materially, the date at the top of this page changes with "
                "it. There is no mailing list, so checking this page is the way to see it."))

    o.append(_h("Contact"))
    o.append(_p(f'<a href="mailto:{CONTACT}">{CONTACT}</a>'))
    return "\n".join(o)


# ----------------------------------------------------------------------------- terms
def terms_body():
    o = []
    o.append('  <p class="crumb"><a href="/">ViewPrep</a> / Terms</p>')
    o.append("  <h1>Terms of use</h1>")
    o.append(f'  <p class="meta-line">Last updated {LAST_UPDATED}</p>')

    o.append(_p("By using ViewPrep you agree to these terms. They are deliberately short."))

    o.append(_h("What ViewPrep is, and what it is not"))
    o.append(_p("ViewPrep is a free educational flashcard site covering investment banking and "
                "consulting interview fundamentals. It is an independent project. It is not "
                "affiliated with, endorsed by, or sourced from any university, employer, bank, "
                "consultancy or commercial prep provider."))
    o.append(_p("<b>The content is educational and is not professional advice.</b> Nothing on this "
                "site is financial, investment, legal, tax or career advice, and it must not be "
                "relied on as such. The cards are written to help you learn concepts that come up "
                "in interviews. They are simplified by design, practice varies between firms and "
                "between accounting standards, and material can go out of date."))
    o.append(_p("We try hard to be accurate and correct mistakes when we find them, but we do not "
                "warrant that the content is complete, current or error free, and we do not "
                "promise any outcome. Using ViewPrep will not guarantee you an interview, an "
                "offer, or a correct answer on the day. Check anything that matters against a "
                "primary source."))

    o.append(_h("Accounts"))
    o.append(_ul([
        "You are responsible for keeping your password to yourself.",
        "Use a real email address you control, so you can recover the account.",
        "One person per account.",
        "You can ask for your account to be deleted at any time by emailing us.",
    ]))

    o.append(_h("Acceptable use"))
    o.append(_p("Please do not:"))
    o.append(_ul([
        "scrape, bulk download or systematically copy the card content;",
        "republish or resell the cards, in whole or in part, including inside another app, "
        "deck or paid course;",
        "attempt to break, overload or gain unauthorised access to the site or its database;",
        "use the site to break the law.",
    ]))
    o.append(_p("Studying the cards, sharing a link, and telling other people about the site are "
                "all actively encouraged."))

    o.append(_h("Who owns what"))
    o.append(_p("All flashcard content, text and design on ViewPrep is owned by "
                "the site's author and remains theirs. You get a personal, non-transferable right "
                "to use it to study. That right does not include redistribution."))

    o.append(_h("Availability"))
    o.append(_p("The site is free and provided as is. It may be changed, interrupted or "
                "discontinued at any time without notice. Keep your own notes if something here "
                "matters to you."))

    o.append(_h("Liability"))
    o.append(_p("To the fullest extent the law allows, we are not liable for any loss arising from "
                "your use of the site, including any interview or career outcome. Nothing here "
                "excludes liability that cannot legally be excluded."))

    o.append(_h("Governing law"))
    o.append(_p("These terms are governed by the laws of Portugal."))

    o.append(_h("Contact"))
    o.append(_p(f'<a href="mailto:{CONTACT}">{CONTACT}</a>'))
    return "\n".join(o)


# ------------------------------------------------------------------------------- faq
FAQ = [
    ("Is ViewPrep really free?",
     "Yes, completely. All 618 cards across all 38 decks are free, there is no paid tier, no "
     "trial, and no card is held back behind an account."),
    ("Do I need an account?",
     "No. You can study every card signed out, and your progress is saved in your browser. An "
     "account only adds two things: your progress survives clearing your browser data, and it "
     "follows you between your phone and your laptop."),
    ("Do I need a finance background to use it?",
     "No, and that is the point. Every deck is sequenced from the most basic concept to the more "
     "demanding ones, so you can start at accounting fundamentals knowing nothing and work "
     "upward. Most interview prep material assumes you already speak the language."),
    ("How does the review scheduling work?",
     "After each card you choose Again, Good or Easy. Again brings the card back the same day, "
     "Good in three days, Easy in a week. Cards you find difficult come round more often, and "
     "cards you know get out of your way. The intervals are fixed and predictable rather than "
     "adaptive, because you are preparing over weeks, not years."),
    ("What is on the cards?",
     "Accounting, financial statements, valuation, M&amp;A, LBOs, capital markets, debt and "
     "credit, and Excel modelling on the investment banking side. Case structuring, market "
     "sizing, microeconomics, profitability, pricing, marketing, strategy frameworks and "
     "operations on the consulting side, plus a deck on each interview process itself."),
    ("Is this for UK spring weeks and internships?",
     "It suits any early finance or consulting interview. It was built during a UK spring week "
     "cycle, so the coverage leans towards the technical questions asked at first-year insight "
     "programmes, summer internships and graduate interviews."),
    ("Can I use it on my phone?",
     "Yes. The site is built to work on a phone, which is where most people actually revise."),
    ("How is this different from Anki?",
     "Anki is a powerful empty container: you supply the cards. ViewPrep ships 618 cards already "
     "written and ordered, so there is nothing to build before you can start. If you already have "
     "a deck you like, Anki is excellent."),
    ("Will you add more cards?",
     "Yes. New decks and cards get added over time. Nothing that is free today will move behind "
     "a paywall later."),
    ("How do I delete my account and data?",
     'Email <a href="mailto:%s">%s</a> and ask. Your account, your synced progress and any usage '
     "events tied to it are removed." % (CONTACT, CONTACT)),
    ("Can I suggest a correction?",
     'Please do. If a card is wrong or misleading, email <a href="mailto:%s">%s</a> with the deck '
     "and the card, and it gets fixed. A confidently wrong answer in an interview is worse than "
     "no answer, so corrections are genuinely welcome." % (CONTACT, CONTACT)),
]


def faq_body():
    o = []
    o.append('  <p class="crumb"><a href="/">ViewPrep</a> / FAQ</p>')
    o.append("  <h1>Frequently asked questions</h1>")
    o.append(_p("Everything people ask before they start. If your question is not here, email "
                f'<a href="mailto:{CONTACT}">{CONTACT}</a>.'))
    for q, a in FAQ:
        o.append(f"  <h2>{q}</h2>")
        o.append(f"  <p>{a}</p>")
    o.append('  <div class="cta-block">')
    o.append("    <h2>Start with a card, not a sales page</h2>")
    o.append("    <p>Every deck is open. Pick one and see whether it fits how you think.</p>")
    o.append('    <a class="btn" href="/">Study the cards</a>')
    o.append("  </div>")
    return "\n".join(o)


def faq_jsonld():
    """FAQPage structured data. Strips the HTML we allow in answers, since the
    schema expects text and search engines show it raw."""
    import re

    def plain(html):
        return re.sub(r"<[^>]+>", "", html).replace("&amp;", "&").replace("&ccedil;", "c")

    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": plain(q),
             "acceptedAnswer": {"@type": "Answer", "text": plain(a)}}
            for q, a in FAQ
        ],
    }


# --------------------------------------------------------------------------- 404
def notfound_body():
    o = []
    o.append('  <p class="crumb"><a href="/">ViewPrep</a> / Not found</p>')
    o.append("  <h1>That page does not exist</h1>")
    o.append(_p("The link was probably mistyped, or it pointed at something that has since "
                "moved. Nothing is broken; this address just has nothing behind it."))
    o.append(_h("Try one of these instead"))
    o.append(_ul([
        '<a href="/">Start studying</a> &ndash; 618 free cards, no account needed',
        '<a href="/decks/">Every deck</a> &ndash; browse all 38 and read the cards as text',
        '<a href="/faq.html">FAQ</a> &ndash; what this is and how the review scheduling works',
    ]))
    o.append('  <div class="cta-block">')
    o.append("    <h2>Or just pick a card</h2>")
    o.append(_p("Investment banking and consulting interview fundamentals, one card at a time."))
    o.append('    <a class="btn" href="/">Study the cards</a>')
    o.append("  </div>")
    return "\n".join(o)


# ------------------------------------------------------- commercial awareness
# Deliberately a guide and not a deck. Commercial awareness is a habit and a way
# of talking, not a set of facts that can be memorised off a flashcard, and a
# card written today about a live market would be wrong within a month.
def commercial_body():
    o = []
    o.append('  <p class="crumb"><a href="/">ViewPrep</a> / Commercial awareness</p>')
    o.append("  <h1>Commercial awareness, without the panic</h1>")
    o.append(_p("Every investment banking and consulting interview contains a version of the same "
                "question: what is going on out there, and why do you care. It is the part most "
                "candidates prepare last and lose points on first. This is a guide rather than a "
                "deck, because commercial awareness is a habit and a way of talking. A flashcard "
                "that told you what interest rates are today would be wrong by the time you "
                "sat the interview."))
    o.append(_h("What the question is actually testing"))
    o.append(_p("Nobody expects a first-year to have a view the desk does not already have. The "
                "interviewer is checking three things: that you read something without being told "
                "to, that you can explain it to someone who has not read it, and that you "
                "understand why it matters to the person sitting opposite you. A candidate who "
                "recites a headline fails all three. A candidate who takes one story and says "
                "plainly what happened, why it happened now, and what it changes for a bank or a "
                "client passes all three, even if the story is small."))
    o.append(_p("So the goal is not coverage. It is one or two stories you can actually hold a "
                "conversation about, plus enough of the landscape that you are not surprised by a "
                "follow-up."))
    o.append(_h("The weekly habit"))
    o.append(_p("Twenty minutes a day, or an hour on a Sunday, is enough. Read a general business "
                "paper for the front section and the companies pages, and pick one story a week "
                "to go deeper on. Keep a single page of notes with three headings: what moved in "
                "markets, one deal, one company or sector story. Write two sentences under each, "
                "in your own words. The writing is the part that makes it stick, and the page is "
                "what you re-read on the train to the interview."))
    o.append(_p("By the fourth week you will notice the same forces turning up under different "
                "headlines, which is the point at which it stops being revision and starts being "
                "awareness."))
    o.append(_h("How to talk about a deal"))
    o.append(_p("Most banking interviews ask for a deal you have followed. Use the same five beats "
                "every time and you will never ramble:"))
    o.append(_ul([
        "<b>What happened.</b> Who bought whom, for how much, announced when, cash or shares.",
        "<b>Why now.</b> The commercial reason: consolidation in a shrinking market, a capability "
        "the buyer could not build in time, a founder wanting out, a sponsor at the end of its hold.",
        "<b>How it was paid for.</b> Cash off the balance sheet, new debt, issuing shares, or a "
        "mix, and what that says about how confident the buyer is.",
        "<b>What the market made of it.</b> Which share price moved and in which direction, and "
        "the honest reading of that: a buyer falling on announcement usually means the market "
        "thinks they paid too much or doubts the synergies.",
        "<b>Your view.</b> One sentence, with a reason, and one thing that would change your mind.",
    ]))
    o.append(_p("Pick a deal in a sector the bank actually covers, and pick one small enough that "
                "you can hold the detail. A mid-sized deal you can discuss properly beats the "
                "largest deal of the year discussed vaguely."))
    o.append(_h("How to talk about markets"))
    o.append(_p("Macro questions sound open-ended but almost always want the same chain: what the "
                "central bank is doing with rates, what that does to the cost of borrowing, what "
                "that does to valuations and to the volume of deals, and who it helps or hurts. "
                "Higher rates raise the discount rate, so future cash flows are worth less today, "
                "which drags on valuations and hits long-duration, high-growth companies hardest. "
                "They also make debt more expensive, which narrows what a buyout can pay and slows "
                "leveraged deal activity. Falling rates run the same chain in reverse."))
    o.append(_p("You do not need the exact rate to the decimal, though knowing roughly where it is "
                "and which way it last moved is the minimum. What you need is the chain, because "
                "the follow-up is almost always “and what does that mean for us?”"))
    o.append(_h("The consulting version"))
    o.append(_p("Consulting interviews rarely ask about deals. They ask what industry interests "
                "you, or what you would worry about if you ran a business in it. The structure is "
                "the same but the lens is the client’s: what is happening to demand, what is "
                "happening to costs, what technology or regulation is changing the economics, and "
                "what the firms in that industry are doing about it. Bring one industry you "
                "genuinely find interesting and be able to name two or three forces reshaping it, "
                "with a consequence attached to each. That is indistinguishable from the opening "
                "of a good case."))
    o.append(_h("Before the interview"))
    o.append(_p("Read the firm’s own recent announcements and the sectors its office is known "
                "for, so that when you are asked why this firm you are not guessing. Re-read your "
                "one page. Have your deal or industry story ready in two lengths, a thirty-second "
                "version and a two-minute version, because you will not know which one the room "
                "wants until you are in it. And if you are asked about something you have not "
                "followed, say so and offer what you have followed instead. That reads as honest, "
                "which is worth more than a bluffed answer that collapses on the second question."))
    o.append('  <div class="cta-block">')
    o.append("    <h2>The technical half</h2>")
    o.append(_p("Commercial awareness carries one half of the interview. The cards carry the other."))
    o.append('    <a class="btn" href="/">Study the cards</a>')
    o.append("  </div>")
    return "\n".join(o)


PAGES = [
    # slug, title, description, body fn, jsonld fn or None, sitemap priority
    ("faq.html", "Frequently asked questions | ViewPrep",
     "Is ViewPrep free, do you need an account, what is on the cards, and how the spaced "
     "review scheduling works.", faq_body, faq_jsonld, "0.7"),
    ("privacy.html", "Privacy policy | ViewPrep",
     "What ViewPrep stores, where it goes, which third parties see anything, and how to have "
     "your data deleted.", privacy_body, None, "0.3"),
    ("404.html", "Page not found | ViewPrep",
     "That page does not exist. Browse the decks or start studying 618 free investment "
     "banking and consulting interview flashcards.", notfound_body, None, None),
    ("commercial-awareness.html", "Commercial awareness for banking and consulting interviews | ViewPrep",
     "How to build commercial awareness for an investment banking or consulting interview: the "
     "weekly habit, how to talk about a deal, and how rates feed through to valuations.",
     commercial_body, None, "0.7"),
    ("terms.html", "Terms of use | ViewPrep",
     "Terms of use for ViewPrep, including the educational content disclaimer and acceptable "
     "use.", terms_body, None, "0.3"),
]
