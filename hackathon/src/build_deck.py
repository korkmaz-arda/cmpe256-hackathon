"""Build a presentation slide deck for the hackathon project.

Monochrome design (black text on white) per the user's formatting rules.
Run: venv/bin/python src/build_deck.py  -> submission/Hackathon_Deck.pptx
"""
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
BLACK = RGBColor(0, 0, 0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY = RGBColor(0xF2, 0xF2, 0xF2)
DARKGRAY = RGBColor(0, 0, 0)  # kept as a name; user rule: all text black

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def new_slide():
    return prs.slides.add_slide(BLANK)


def textbox(slide, x, y, w, h):
    return slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))


def set_text(shape, lines, sizes=(28,), bolds=(True,), aligns=None,
             color=BLACK, space_after=6):
    """lines: list of strings; sizes/bolds cycle per line."""
    tf = shape.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.space_before = Pt(0)
        if aligns:
            p.alignment = aligns[i % len(aligns)]
        run = p.add_run()
        run.text = line
        run.font.size = Pt(sizes[i % len(sizes)])
        run.font.bold = bolds[i % len(bolds)]
        run.font.color.rgb = color
        run.font.name = "Calibri"
    return shape


def title_slide(slide, kicker, title, subtitle):
    set_text(textbox(slide, 0.8, 0.6, 11.7, 1.0), [kicker],
             sizes=(18,), bolds=(True,), color=DARKGRAY)
    set_text(textbox(slide, 0.8, 1.5, 11.7, 2.6), [title],
             sizes=(44,), bolds=(True,))
    set_text(textbox(slide, 0.8, 4.2, 11.7, 2.4), subtitle,
             sizes=(22,), bolds=(False,), color=DARKGRAY)


def section_slide(slide, label, heading, bullets):
    set_text(textbox(slide, 0.8, 0.5, 11.7, 0.8), [label],
             sizes=(16,), bolds=(True,), color=DARKGRAY)
    set_text(textbox(slide, 0.8, 1.2, 11.7, 1.2), [heading],
             sizes=(32,), bolds=(True,))
    box = textbox(slide, 0.8, 2.7, 11.7, 4.3)
    tf = box.text_frame
    tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(10)
        p.level = 0
        run = p.add_run()
        run.text = "\u2022  " + b
        run.font.size = Pt(20)
        run.font.color.rgb = BLACK
        run.font.name = "Calibri"


def box(slide, x, y, w, h, text, size=16, bold=True, fill=WHITE,
        font_color=BLACK):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                   Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = BLACK
    shape.line.width = Pt(1.5)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = font_color
    run.font.name = "Calibri"
    return shape


def arrow(slide, x1, y1, x2, y2):
    conn = slide.shapes.add_connector(1, Inches(x1), Inches(y1),
                                      Inches(x2), Inches(y2))
    conn.line.color.rgb = BLACK
    conn.line.width = Pt(1.5)
    return conn


# ---------- 1. Title ----------
s = new_slide()
title_slide(s, "CMPE 256 HACKATHON  \u2014  SJSU, OCTOBER 2026",
            "Agentic AI Management\nConsulting Platform",
            ["Pranith Varma Pakalapati",
             "From student to entrepreneur: intelligent AI coworkers for "
             "enterprise decision-making"])

# ---------- 2. Concept ----------
s = new_slide()
section_slide(s, "THE CONCEPT",
              "A consulting firm, not a chatbot",
              ["One Manager Agent takes the customer's question and routes it "
               "to specialist domain agents",
               "Each agent answers from authoritative documents \u2014 not from "
               "the model's memory",
               "Findings are consolidated into recommendations with evidence, "
               "confidence levels, and measurable next actions"])

# ---------- 3. Architecture diagram ----------
s = new_slide()
set_text(textbox(s, 0.8, 0.4, 11.7, 0.8), ["ARCHITECTURE"],
         sizes=(16,), bolds=(True,), color=DARKGRAY)
set_text(textbox(s, 0.8, 1.0, 11.7, 1.0),
         ["Hierarchical multi-agent orchestration"],
         sizes=(30,), bolds=(True,))
box(s, 5.2, 2.2, 2.9, 1.0, "Management Consulting\nManager Agent",
    size=15, fill=GRAY)
set_text(textbox(s, 5.2, 3.25, 2.9, 0.4),
         ["intent detection \u2022 routing \u2022 orchestration"],
         sizes=(11,), bolds=(False,), color=DARKGRAY,
         aligns=(PP_ALIGN.CENTER,))
agents = [("Technology\nAgent", "Cisco \u2022 Google Cloud"),
          ("Clinical\nAgent", "Agilent diagnostics"),
          ("SEC\nAgent", "2025 filings"),
          ("Corporate Resp.\nAgent", "food security")]
for i, (name, sub) in enumerate(agents):
    x = 0.7 + i * 3.05
    box(s, x, 4.1, 2.7, 1.1, name, size=14)
    set_text(textbox(s, x, 5.25, 2.7, 0.4), [sub], sizes=(11,),
             bolds=(False,), color=DARKGRAY, aligns=(PP_ALIGN.CENTER,))
    arrow(s, 6.65, 3.2, x + 1.35, 4.1)
box(s, 3.9, 6.0, 5.5, 0.9, "Consulting recommendation", size=16, fill=GRAY)
set_text(textbox(s, 3.9, 6.9, 5.5, 0.35),
         ["evidence \u2022 insights \u2022 next actions"],
         sizes=(11,), bolds=(False,), color=DARKGRAY,
         aligns=(PP_ALIGN.CENTER,))

# ---------- 4. Domain agents ----------
s = new_slide()
section_slide(s, "KNOWLEDGE",
              "Four specialists, four corpora",
              ["Technology \u2014 Cisco router documentation, Google Cloud guides, "
               "and a 1,000-transaction procurement catalog",
               "Clinical \u2014 Agilent Seahorse, NanoZoomer, and Artisan product "
               "documentation",
               "SEC \u2014 Cisco, Alphabet, and Agilent 2025 SEC filings "
               "(10-K risk factors, financials)",
               "Corporate Responsibility \u2014 FAO State of Food Security reports "
               "2023 and 2024",
               "Total: about 9,300 chunked passages, each cited by source"])

# ---------- 5. How it works ----------
s = new_slide()
section_slide(s, "HOW IT WORKS",
              "Grounded answers, ranked recommendations",
              ["Retrieval-augmented generation: per-domain TF-IDF retrieval, "
               "every finding cited as [source #chunk-id]",
               "Recommender: association-rule mining over procurement history "
               "\u2014 296 rules with support, confidence, and lift",
               "Explainability: confirmed findings separated from hypotheses; "
               "uncertainty flags when evidence is thin",
               "Ambiguity handled: the manager asks for clarification instead "
               "of guessing"])

# ---------- 5b. Agent prompts ----------
s = new_slide()
set_text(textbox(s, 0.8, 0.4, 11.7, 0.8), ["AGENT PROMPTS"],
         sizes=(16,), bolds=(True,), color=DARKGRAY)
set_text(textbox(s, 0.8, 1.0, 11.7, 1.0),
         ["Every agent ships with an explicit instruction set"],
         sizes=(30,), bolds=(True,))
prompts = [
    ("Manager", "Partner of the firm. Do: detect intent, route (multi-label), "
     "consolidate with evidence and next actions, ask when ambiguous. "
     "Don't: answer directly, invent evidence, hide uncertainty."),
    ("Technology", "Senior network consultant. Do: cite Cisco/GCP docs, separate "
     "confirmed faults from hypotheses, ask for missing diagnostics. Don't: "
     "assume a part failed, recommend incompatible parts."),
    ("Clinical", "Diagnostics consultant. Do: match assays to Agilent lines, "
     "cite product docs, IEEE papers, trial registry. Don't: give patient "
     "advice, overstate trial evidence."),
    ("SEC", "Risk analyst. Do: extract 10-K risk factors, bucket "
     "financial/competitive/operational, cite filings. Don't: give investment "
     "advice, invent numbers, mix companies."),
    ("CSR", "ESG advisor. Do: ground in SOFI reports, link tech investments to "
     "food-security outcomes. Don't: invent statistics or ESG claims."),
]
box = textbox(s, 0.8, 2.2, 11.7, 4.8)
tf = box.text_frame
tf.word_wrap = True
for i, (name, desc) in enumerate(prompts):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(10)
    r1 = p.add_run()
    r1.text = name + ": "
    r1.font.size = Pt(17)
    r1.font.bold = True
    r1.font.color.rgb = BLACK
    r1.font.name = "Calibri"
    r2 = p.add_run()
    r2.text = desc
    r2.font.size = Pt(17)
    r2.font.color.rgb = BLACK
    r2.font.name = "Calibri"

# ---------- 5c. Part B ----------
s = new_slide()
section_slide(s, "PART B  \u2014  MARKET BASKET",
              "Whole-cart recommendations, honestly blank when unsure",
              ["Single-page UI: full 40-product list stays visible, add to cart, "
               "recommendations appear below",
               "Apriori with min support 2 baskets, min confidence 0.10, lift > 1 "
               "\u2014 2,181 rules mined",
               "Rules fire on the whole cart only \u2014 no partial-basket fallback",
               "No covering pattern \u2192 the panel blanks out, even if a smaller "
               "cart had recommendations",
               "Demo: two cameras \u2192 keypad recommended; D7050 + PG9914 \u2192 "
               "blank (they co-occur in only 5 baskets)",
               "Open partb/market_basket.html \u2014 no server needed"])
s = new_slide()
section_slide(s, "DEMO  \u2014  THE BRIEF'S EXAMPLE",
              "\u201cOur Cisco router keeps dropping connections\u2026\u201d",
              ["Routed to the Technology Agent with high confidence",
               "Retrieves Cisco troubleshooting docs: WAN errors, SD-WAN "
               "misconfiguration, power redundancy, overheating",
               "Asks for missing diagnostics before any part is ordered \u2014 "
               "hypotheses are labeled, not assumed",
               "Manager consolidates: remediation steps, procurement priority, "
               "preventive maintenance, each with impact and a metric"])

# ---------- 7. Demo: cross-domain ----------
s = new_slide()
section_slide(s, "DEMO  \u2014  CROSS-DOMAIN",
              "One question, three agents",
              ["\u201cEvaluate Cisco as a strategic vendor: products, financial "
               "risks, sustainability alignment\u201d",
               "SEC Agent cites disclosed risk factors from the 10-K",
               "Technology Agent cites product documentation",
               "Corporate Responsibility Agent anchors sustainability to FAO "
               "reports \u2014 merged into a single recommendation"])

# ---------- 8. Results ----------
s = new_slide()
section_slide(s, "MEASURED RESULTS",
              "Evaluated, not asserted",
              ["Routing: 24/24 correct on single- and cross-domain queries "
               "(F1 1.0)",
               "Retrieval: cross-domain precision@5 of 0.825 \u2014 the right "
               "domain's evidence wins even when all four corpora compete",
               "Recommendation: 296 rules mined; hit-rate@5 of 0.27, MRR@5 of "
               "0.128 on 200 hold-one-out tests",
               "Honest reporting: modest recommender scores are shown as-is; "
               "sparse co-purchase data limits rule coverage"])

# ---------- 9. Business value ----------
s = new_slide()
section_slide(s, "BUSINESS VALUE",
              "Every answer ends with what to do next",
              ["Each recommendation states the action, why it fits, the "
               "expected impact, and how to measure it",
               "Uncertainty is flagged where evidence is thin \u2014 customers "
               "see what is verified and what still needs checking",
               "Progress is observable rather than assumed"])

# ---------- 10. Run it ----------
s = new_slide()
section_slide(s, "TRY IT",
              "Runs anywhere \u2014 no API keys",
              ["venv/bin/python src/kb_build.py   \u2014  build the knowledge base",
               "venv/bin/python src/demo.py   \u2014  7 demo cases",
               "venv/bin/python src/evaluate.py   \u2014  full metrics",
               "venv/bin/python src/build_submission.py   \u2014  rebuild this write-up",
               "Local CPU only. Prototype at github-style layout: src / data / "
               "results / submission."])

out = ROOT / "submission" / "CMPE256_Hackathon_Deck.pptx"
prs.save(out)
print("wrote", out, "-", len(prs.slides.__iter__.__self__._sldIdLst), "slides")
