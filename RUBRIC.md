# CMPE 256 Hackathon: Rubric (confirmed in the Oct 17 meetings)

Based on what the professor said in both meetings on Oct 17 (the morning kickoff and the 1:30 Q&A). The pre-meeting guesswork is saved in `notes/RUBRIC_pre-meeting.md`.

> **Due before 1:30 PM Sunday, Oct 18, 2026, on Canvas.** The assignment closes at 1:30.

---

## How it's graded

- **Done or not done.** The professor said: if you demo a cross-domain interaction in your presentation, you'll get "a considerable grade, which is full."
- **What they'll look at:**
  1. Each agent's **prompt / instruction set**
  2. **How each agent is grounded**, shown during the demo
  3. **The full code base**: they'll check how you did RAG and the recommendations
  4. **Cross-domain results**
- **Nobody mentioned an automated grader.** The professor said they'd watch the video and check the code.
- **Why it matters beyond this grade:** doing well on the hackathon, the midterm and the final project makes the **final exam optional**. That was said on the recording. Teamwork counts more than individual work.

---

## What to submit (2 things)

1. **A zip of the entire source code, uploaded to Canvas.** No GitHub or GCP links. If you work in GitHub, download the final version and upload the zip.
2. **A group video, 5–7 minutes.** The morning meeting said 6 minutes max, so aim for 6.

   | Time | Content |
   |---|---|
   | ~1 min | Intro and **architecture** |
   | ~4 min | **Agents**: each agent's prompt/instructions, its grounding, then the live demo (prompts → responses), including a **cross-domain** query |
   | ~2 min | **Market basket** (only if you built it) |

Next class (Monday) there's also a very brief in-class demo.

---

## Part A: Multi-agent consulting platform (required, "90% priority")

- [ ] **Manager / router agent** that detects intent and routes to the right specialist.
  - The professor's suggestion: a **mini model** for routing, then a **full reasoning model** inside the chosen specialist.
- [ ] **Specialist agents:** Technology, Clinical, SEC, Corporate Responsibility (Food Security).
  - Aim for all four, but **"two done well is much better than all [four] not coherent."**
  - If you only finish two, say in the video that the other two use the same template.
- [ ] **For each agent, write down and show:**
  - persona
  - instructions (what to do and what not to do)
  - domain expertise
  - grounding sources
- [ ] **Grounding uses both kinds of source**, through RAG or by putting documents in the prompt. They hold different information.
  - **.zip files:** the local PDFs and CSVs
  - **.txt files:** links to web pages and PDFs you have to fetch
  - Using other internet sources is allowed.
- [ ] **At least one cross-domain query**, where two or more agents work on one question.
- [ ] **Demo of real prompts → responses** (see the prompts list below).

**Freedom:** any language, framework, architecture or model, including local models like Ollama. Coding agents are fine. Hosting isn't required; the video is enough.

---

## Part B: Market basket recommender (optional, "if time permits")

The **remaining ~2 min** of the video, if you build it. You can split into sub-teams.

- [ ] A simple UI **or** a Jupyter notebook. Putting it on the same web page as Part A in a separate tab is fine.
- [ ] The full product list stays visible and unfiltered.
- [ ] Add an item → it goes into the cart → recommendations appear **below** it.
- [ ] Use **Apriori from class** (support / confidence).
- [ ] **Recommend from the whole cart only.**
  - If the cart's combination has no frequent itemset that meets your thresholds, **show nothing**. That holds even if earlier steps had recommendations.
  - The professor's example: "camera and banana" → blank.

**Watch out if you reuse your ARM homework:**

- It falls back to rules from part of the basket. The professor said not to, so remove that fallback.
- Its thresholds (confidence 0.20, lift 3.0) give **zero** recommendations for any first item on this data. Use a lower confidence floor and lift > 1.
- With a minimum support of 5 baskets, almost every 2-item cart will come up blank. Consider a lower minimum, like 2 baskets.
- For the video, show one cart path that gets recommendations and one that blanks out. That covers both required behaviours.
- The slide's own demo cart blanks out after the second item: *Bosch D7050* + *DSC PG9914* appear together in only 5 baskets, and every other item appears with them just once. That's the correct behaviour.

---

## Questions the meetings settled

| Question | Answer |
|---|---|
| Do we have to do both parts? | Multi-agent is required. Market basket is optional. |
| All four agents? | Do your best. Two done well beats four done badly. Include at least one cross-domain interaction. |
| What's the rubric? | Done / not done, with a cross-domain demo. Deliverables: agent prompts, grounding, code, cross-domain results. |
| Ground on the .zip or the .txt files? | Both. They're different information. |
| Which companies for SEC? | **Alphabet, Agilent and Cisco**, fiscal years 2025–2026. Use all the filings. |
| Which model? | Your choice. Local is fine. |
| Do we have to host it? | No. The video is enough. |
| Both parts on one page? | Fine. Use tabs or two sections. |
| Questions over the weekend? | Canvas discussion forum or email. Expect a reply within about 2–3 hours. |

## Questions nobody asked (best guesses; no need to ask)

- **IBM:** there's no data for it, so skip it and say so in one line of the video.
- **Agilent "manuals":** ground the Clinical agent on the web pages in `Agilent.txt`, the IEEE papers and the trial CSVs.
  - Good demo: "we need to measure mitochondrial function in a diabetes study" → recommend the **Seahorse XF**. 11 trials in the CSVs use it.
- **Google:** ground on the GCP pages in `Google GCP.txt`, as the professor said.

---

## Demo prompts to run in the video

**Food Security (from slide 4):**
- "List major Food insecurity reason in 2023 from within the context of State of Food Security and Nutrition in the World 2023 report."
- "Explain malnutrition in war zones" (SOFI 2023)
- "List major Food insecurity reason in 2024"
- "Explain increase prices impact on food security"

**One per specialist (the professor read these out in the morning meeting):**
- **Technology:** "Which replacement components should we order to resolve a Cisco router failure?"
- **Clinical:** "Which diagnostic instrument or replacement component best meets our laboratory requirements?"
- **SEC:** "What are the financial, competitive, and operational risks associated with these companies?"
- **Corporate Responsibility:** "Which technology investments could improve food security and sustainability outcomes?"

**Cross-domain (write your own).** Example: *"We're considering Cisco Catalyst edge routers to monitor cold-chain food distribution. Which model fits, what risks does Cisco's 10-K disclose, and how would this support food-security outcomes per SOFI 2024?"*

---

## Data reference

| Folder | What's in it |
|---|---|
| `data/Clinical/` | 20 IEEE papers (COVID, diabetes, heart attack, knee) and 4 ClinicalTrials.gov CSVs with 32,611 studies |
| `data/SEC/` | 10-Ks: Agilent FY2025, Cisco FY2025 + FY2026, Alphabet FY2024 + FY2025 |
| `data/FoodSecurity/` | UN FAO SOFI 2023 and 2024 reports |
| `data/Retail/` | 1,000 baskets, 40 security-hardware SKUs, 2–5 items each |
| `sources/*.txt` | Links: 5 Cisco router datasheets, 4 Agilent product pages, 3 GCP pages (MCP, RAG) |
