# Hackathon video script — 6 minutes, group presentation
Slide numbers refer to submission/CMPE256_Hackathon_Deck.pptx.
Rotate speakers (teamwork counts). Screen-record the terminal/browser for demos.

## 0:00–0:45 — Intro and architecture (Slides 1–3)
- One speaker: the entrepreneurial framing — an AI consulting firm where a
  Manager Agent routes customer questions to specialist domain agents.
- Show the architecture diagram (Slide 3): manager on top (intent detection,
  routing, orchestration), four specialists, one consolidated recommendation
  with evidence, insights, next actions.
- One line: no IBM data exists, so the Technology agent covers Cisco and
  Google Cloud; say this explicitly.

## 0:45–4:30 — Agents: prompt, grounding, live demo (Slides 4–7)
For EACH agent (about 50 seconds each): show the prompt card (Slide 5b),
name its grounding sources, then run the professor's prompt live in the
terminal and scroll the response.

- Technology (~0:45–1:35): prompt card; grounding = Cisco datasheets,
  GCP pages, procurement catalog. Prompt: "Which replacement components
  should we order to resolve a Cisco router failure?" Point out: confirmed
  faults vs hypotheses, diagnostics asked before parts ordered.
- Clinical (~1:35–2:25): prompt card; grounding = Agilent pages, 20 IEEE
  papers, 32,611 ClinicalTrials.gov studies. Prompt: "Which diagnostic
  instrument or replacement component best meets our laboratory
  requirements?" Bonus if time: the Seahorse/diabetes/mitochondrial case,
  citing trial counts.
- SEC (~2:25–3:15): prompt card; grounding = Cisco, Alphabet, Agilent 10-K
  filings. Prompt: "What are the financial, competitive, and operational
  risks associated with these companies?" Point out the risk buckets and
  citations.
- CSR (~3:15–4:00): prompt card; grounding = FAO SOFI 2023/2024. Prompt:
  "Which technology investments could improve food security and
  sustainability outcomes?" Optionally run one SOFI prompt verbatim.
- Cross-domain (~4:00–4:30): "We're considering Cisco Catalyst edge routers
  to monitor cold-chain food distribution. Which model fits, what risks does
  Cisco's 10-K disclose, and how would this support food-security outcomes
  per SOFI 2024?" Show the routing line hitting three agents and the merged
  recommendation. This is the graded moment — do not skip it.

## 4:30–6:00 — Part B: market basket (Slide 5c + live UI)
- Open partb/market_basket.html in a browser. Full 40-product list is
  visible; thresholds shown (min support 2 baskets, confidence 0.10, lift > 1).
- Path 1 (recommendations): click "Demo: cart with recommendations"
  (two cameras). A keypad is recommended with support/confidence/lift.
  Note: rules fire on the whole cart only.
- Path 2 (blank): click "Demo: cart that blanks out" (Bosch D7050 +
  DSC PG9914). Panel goes blank — correct behavior: they co-occur in only
  5 baskets and no third item meets the thresholds with them. Mention the
  professor's "camera and banana" example as the same principle.
- Close: everything runs locally, no API keys; code zip is the Canvas
  submission alongside this video.

## Monday in-class demo (very brief)
- Run the cross-domain query live (30 seconds), then one market-basket
  path. That's the whole thing.
