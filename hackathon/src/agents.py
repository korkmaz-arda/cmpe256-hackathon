"""Multi-agent consulting platform.

ManagerAgent: intent detection (domain-centroid + keyword scoring), routing
(single- or multi-domain), and orchestration (consolidates agent reports
into one consulting recommendation with evidence, insights, next actions).

Domain agents: Technology, Clinical, SEC, Corporate Responsibility.
Each grounds its answer in retrieved evidence with citations, reports a
confidence level, and explicitly separates confirmed findings from
hypotheses / uncertainties.
"""
import json
import re
from pathlib import Path

from retrieval import KnowledgeBase
from recommender import ComponentRecommender

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "kb" / "catalog.json"

DOMAIN_KEYWORDS = {
    "technology": ["cisco", "router", "catalyst", "switch", "network", "gcp",
                   "google cloud", "cloud", "sku", "camera", "nvr",
                   "detector", "panel", "bosch", "hanwha", "procurement",
                   "order", "throughput", "sd-wan", "ipsec", "virtual router",
                   "8000v", "asr", "isr", "connectivity", "outage", "failure",
                   "vendor", "data center", "parts"],
    "clinical": ["agilent", "diagnostic", "pathology", "seahorse", "cell",
                 "metabolic", "laboratory", "lab", "instrument", "scanner",
                 "slide", "stain", "artisan", "nanozoomer", "clinical", "assay"],
    "sec": ["sec", "filing", "10-k", "10k", "financial", "revenue", "earnings",
            "risk", "annual report", "fiscal", "competition", "competitive",
            "operational risk", "disclose", "alphabet", "shareholder",
            "income", "loss"],
    "csr": ["food security", "sustainability", "esg", "hunger", "nutrition",
            "fao", "sofi", "climate", "csr", "malnutrition", "agrifood",
            "corporate responsibility", "social responsibility", "food"],
}

AGENT_NAMES = {
    "technology": "Technology Agent",
    "clinical": "Clinical Agent",
    "sec": "SEC Agent",
    "csr": "Corporate Responsibility Agent",
}

# Every agent's prompt / instruction set: persona, what to do, what NOT to do,
# domain expertise, and grounding sources. Shown in the demo and the video.
AGENT_PROMPTS = {
    "manager": {
        "persona": "You are the Management Consulting Manager Agent, the "
                   "partner of an AI consulting firm. You never answer "
                   "directly; you delegate to specialists and consolidate.",
        "instructions": [
            "Detect the customer intent from each request.",
            "Route to one or more specialist agents; use multi-label routing "
            "when the question spans domains.",
            "Merge agent reports into a single recommendation with evidence, "
            "confidence, uncertainties, and measurable next actions.",
            "Ask for clarification when no domain scores confidently.",
        ],
        "do_not": [
            "Never answer from your own parametric knowledge.",
            "Never invent evidence or citations.",
            "Never hide uncertainty or low confidence.",
        ],
        "expertise": "Intent classification, multi-agent orchestration, "
                     "business-value framing.",
        "grounding": [
            "Shared TF-IDF index over all domain corpora (routing signals).",
            "Consolidation templates (action / why / impact / measure).",
        ],
    },
    "technology": {
        "persona": "You are a senior network-infrastructure consultant. You "
                   "solve enterprise connectivity problems with documented "
                   "specs, not guesses.",
        "instructions": [
            "Retrieve Cisco and Google Cloud documentation relevant to the "
            "request and cite it.",
            "Distinguish confirmed faults from hypotheses.",
            "Ask for missing diagnostics instead of assuming a component "
            "has failed.",
            "Recommend compatible components, verifying against datasheets "
            "and procurement history.",
        ],
        "do_not": [
            "Never assume a component has failed without evidence.",
            "Never recommend a part incompatible with the stated model.",
            "Never answer financial, clinical, or sustainability questions.",
        ],
        "expertise": "Cisco Catalyst/ISR/ASR platforms, SD-WAN, IPsec/VPN "
                     "throughput, Google Cloud networking, procurement "
                     "catalogs, association-rule recommendations.",
        "grounding": [
            "DataSource-Cisco.txt (5 router datasheet links).",
            "Google_GCP.txt (MCP, RAG documentation links).",
            "Fetched vendor pages: cisco.com (Catalyst 8300, ISR 4000 incl. "
            "end-of-sale, ASR 1000), cloud.google.com (RAG).",
            "Procurement catalog: 1,000 transactions, 40 SKUs.",
        ],
    },
    "clinical": {
        "persona": "You are a clinical diagnostics consultant. You match "
                   "laboratory requirements to instruments using product "
                   "documentation and trial evidence.",
        "instructions": [
            "Match the stated assay or workflow to Agilent product lines "
            "(Seahorse XF, NanoZoomer, Artisan).",
            "Cite product documentation, IEEE papers, and the trial registry.",
            "Explain assay fit: what the instrument measures and for which "
            "workloads.",
            "Use trial counts to support adoption claims.",
        ],
        "do_not": [
            "Never give medical advice for individual patients.",
            "Never recommend instruments outside the documented product lines.",
            "Never overstate what the trial evidence shows.",
            "Never answer financial or networking questions.",
        ],
        "expertise": "Seahorse XF real-time cell metabolic analysis, "
                     "NanoZoomer whole-slide imaging, Artisan special stains; "
                     "clinical trial landscape across COVID-19, diabetes, heart "
                     "disease, knee injuries.",
        "grounding": [
            "Agilent.txt (product portfolio links).",
            "Fetched agilent.com pages (Seahorse, NanoZoomer, Artisan).",
            "20 IEEE papers (COVID, diabetes, heart attack, knee).",
            "ClinicalTrials.gov CSVs: 32,611 studies.",
        ],
    },
    "sec": {
        "persona": "You are a financial risk analyst. You read 10-K filings "
                   "the way management wrote them: as disclosures of what "
                   "could go wrong.",
        "instructions": [
            "Extract risk factors directly from the filings and cite them.",
            "Bucket risks into financial, competitive, and operational.",
            "Keep each company's filings separate; compare explicitly.",
            "Recommend mapping each risk to an owner and a metric.",
        ],
        "do_not": [
            "Never give investment advice.",
            "Never invent financial numbers.",
            "Never mix one company's disclosures with another's.",
        ],
        "expertise": "10-K structure, risk-factor analysis, financial / "
                     "competitive / operational risk taxonomy for Cisco, "
                     "Alphabet, Agilent.",
        "grounding": [
            "Cisco SEC filings (2x 10-K).",
            "Alphabet SEC filings (2x 10-K).",
            "Agilent SEC filing (10-K).",
        ],
    },
    "csr": {
        "persona": "You are a sustainability and ESG advisor. You keep every "
                   "claim anchored to authoritative food-security data.",
        "instructions": [
            "Ground all findings in the FAO SOFI reports; cite them.",
            "Link technology investments to concrete food-security outcomes.",
            "Keep ESG claims auditable against published benchmarks.",
        ],
        "do_not": [
            "Never invent hunger or nutrition statistics.",
            "Never make ESG claims beyond what the reports support.",
            "Never answer product-spec or financial questions.",
        ],
        "expertise": "Food security and nutrition, agrifood systems, SOFI "
                     "financing benchmarks for hunger reduction.",
        "grounding": [
            "FAO SOFI 2023: The State of Food Security and Nutrition.",
            "FAO SOFI 2024: financing to end hunger, food insecurity and "
            "malnutrition.",
        ],
    },
}


def format_prompt(domain: str) -> str:
    p = AGENT_PROMPTS[domain]
    name = "Management Consulting Manager Agent" if domain == "manager" \
        else AGENT_NAMES[domain]
    L = [f"### {name}"]
    L.append(f"Persona: {p['persona']}")
    L.append("Instructions (do):")
    L += [f"  - {x}" for x in p["instructions"]]
    L.append("Instructions (do NOT):")
    L += [f"  - {x}" for x in p["do_not"]]
    L.append(f"Domain expertise: {p['expertise']}")
    L.append("Grounding sources:")
    L += [f"  - {x}" for x in p["grounding"]]
    return "\n".join(L)


def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for p in parts:
        p = p.strip()
        if len(p) < 40:
            continue
        if p.startswith("Source:") or p.startswith("http"):
            continue
        if "https://" in p or "Source:" in p or ".html" in p:
            continue  # navigation / attribution junk, not evidence
        out.append(p)
    return out


def key_sentences(chunk_text, query, n=2, max_len=260):
    qtokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    scored = []
    for s in split_sentences(chunk_text):
        st = set(re.findall(r"[a-z0-9]+", s.lower()))
        overlap = len(qtokens & st)
        if overlap:
            scored.append((overlap, s))
    scored.sort(key=lambda x: -x[0])
    out = []
    for _, s in scored[:n]:
        out.append(s if len(s) <= max_len else s[:max_len].rsplit(" ", 1)[0] + "…")
    return out


class DomainAgent:
    domain = ""

    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        self.name = AGENT_NAMES[self.domain]

    def gather(self, query, k=5):
        hits = self.kb.retrieve(query, self.domain, k=k)
        evidence = []
        for chunk, score in hits:
            evidence.append({
                "citation": self.kb.cite(chunk),
                "source": chunk["source"],
                "score": round(score, 3),
                "text": chunk["text"],
                "excerpt": chunk["text"][:240].replace("\n", " "),
                "key_points": key_sentences(chunk["text"], query),
            })
        return evidence

    def confidence_of(self, evidence):
        if not evidence:
            return 0.0, ["no relevant evidence retrieved in this domain"]
        top = evidence[0]["score"]
        unc = []
        if top < 0.06:
            unc.append("limited evidence: top retrieval score is low, "
                       "findings are tentative")
        if len(evidence) < 3:
            unc.append("thin evidence base: fewer than 3 supporting passages")
        return round(min(0.95, 0.35 + top * 2), 2), unc

    def analyze(self, query):
        raise NotImplementedError


class TechnologyAgent(DomainAgent):
    domain = "technology"

    def __init__(self, kb, recommender: ComponentRecommender):
        super().__init__(kb)
        self.recommender = recommender
        with open(CATALOG_PATH, encoding="utf-8") as f:
            self.catalog = json.load(f)

    def seed_items(self, query):
        qtokens = set(re.findall(r"[a-z0-9]+", query.lower()))
        seeds = []
        for c in self.catalog:
            name_tokens = set(re.findall(r"[a-z0-9]+", c["name"].lower()))
            brand = name_tokens & {"hanwha", "bosch", "pelco", "dahua",
                                   "honeywell", "dsc", "ge"}
            generic = (qtokens & name_tokens) - {"the", "a", "an", "for",
                                                 "with", "and"}
            if brand and len(generic) >= 2:
                seeds.append(c["name"])
            elif len(qtokens & name_tokens) >= 3:
                seeds.append(c["name"])
        return seeds[:3]

    def analyze(self, query):
        evidence = self.gather(query, k=5)
        conf, unc = self.confidence_of(evidence)
        findings, recommendations = [], []
        for ev in evidence[:3]:
            for kp in ev["key_points"][:2]:
                findings.append(f"{kp} {ev['citation']}")
        # component recommendations from procurement history
        seeds = self.seed_items(query)
        recs = self.recommender.recommend(seeds, topn=5) if seeds else []
        for r in recs:
            recommendations.append({
                "action": f"Consider procuring: {r['item']}",
                "why": r["because"] +
                       f" (support {r['support']}, confidence {r['confidence']}, "
                       f"lift {r['lift']})",
                "evidence": ["procurement history: 1,000 transactions"],
                "kind": "hypothesis",
                "expected_impact": "fewer compatibility surprises and repeat orders",
                "how_to_measure": "track return/RMA rate on ordered components",
            })
        if seeds and not recs:
            unc.append("no co-procurement patterns found for the identified items")
        if not seeds:
            unc.append("no catalog items matched the request; component "
                       "recommendations need a product name or SKU")
        recommendations.append({
            "action": "Verify compatibility against the vendor datasheet before ordering",
            "why": "datasheet specs are the authoritative compatibility source",
            "evidence": [e["citation"] for e in evidence[:2]],
            "kind": "confirmed practice",
            "expected_impact": "avoids mis-ordered parts",
            "how_to_measure": "order accuracy rate",
        })
        return {"agent": self.name, "evidence": evidence, "findings": findings,
                "recommendations": recommendations, "confidence": conf,
                "uncertainties": unc}


class ClinicalAgent(DomainAgent):
    domain = "clinical"

    PRODUCTS = {
        "seahorse": "Seahorse XF Real-Time Cell Metabolic Analysis",
        "metabolic": "Seahorse XF Real-Time Cell Metabolic Analysis",
        "nanozoomer": "NanoZoomer 360MD Slide Scanner System (digital pathology)",
        "whole slide": "NanoZoomer 360MD Slide Scanner System (digital pathology)",
        "whole-slide": "NanoZoomer 360MD Slide Scanner System (digital pathology)",
        "artisan": "Artisan Link Pro Special Staining System",
        "stain": "Artisan Link Pro Special Staining System",
        "digital pathology": "Digital pathology scanners / whole-slide imaging",
    }

    def analyze(self, query):
        evidence = self.gather(query, k=5)
        conf, unc = self.confidence_of(evidence)
        findings, recommendations = [], []
        for ev in evidence[:3]:
            for kp in ev["key_points"][:2]:
                findings.append(f"{kp} {ev['citation']}")
        ql = query.lower()
        matched = [label for key, label in self.PRODUCTS.items() if key in ql]
        for label in matched:
            recommendations.append({
                "action": f"Evaluate {label} against the lab's requirements",
                "why": "product line matches the stated laboratory need",
                "evidence": [e["citation"] for e in evidence[:2]],
                "kind": "hypothesis",
                "expected_impact": "better fit between instrument and assay workload",
                "how_to_measure": "throughput per shift and re-run rate after adoption",
            })
        if not matched:
            unc.append("no specific Agilent product matched; request names an "
                       "assay or workflow for a precise recommendation")
            recommendations.append({
                "action": "Shortlist Agilent Seahorse, NanoZoomer, and Artisan lines "
                          "by assay type and sample volume",
                "why": "these are the documented Agilent clinical product lines",
                "evidence": [e["citation"] for e in evidence[:1]],
                "kind": "hypothesis",
                "expected_impact": "structured vendor comparison",
                "how_to_measure": "requirements coverage score per candidate",
            })
        return {"agent": self.name, "evidence": evidence, "findings": findings,
                "recommendations": recommendations, "confidence": conf,
                "uncertainties": unc}


class SECAgent(DomainAgent):
    domain = "sec"

    RISK_BUCKETS = {
        "financial": ["revenue", "margin", "earnings", "debt", "cash flow",
                      "impairment", "currency", "tax"],
        "competitive": ["competition", "competitive", "market share",
                        "pricing pressure", "rival"],
        "operational": ["supply chain", "operations", "cybersecurity",
                        "disruption", "manufacturing", "talent", "outage"],
    }

    def analyze(self, query):
        q = query + " risk factors financial competition operations"
        evidence = self.gather(q, k=8)
        conf, unc = self.confidence_of(evidence)
        findings, recommendations = [], []
        buckets = {b: [] for b in self.RISK_BUCKETS}
        for ev in evidence:
            for s in split_sentences(ev["text"]):
                sl = s.lower()
                if "risk" not in sl:
                    continue
                for b, kws in self.RISK_BUCKETS.items():
                    if any(k in sl for k in kws):
                        s = s[:260].rsplit(" ", 1)[0] + "…"
                        buckets[b].append((s, ev["citation"]))
                        break
        for b, items in buckets.items():
            seen = set()
            for s, cite in items[:2]:
                key = s[:60]
                if key not in seen:
                    seen.add(key)
                    findings.append(f"[{b} risk] {s} {cite}")
        if not findings:
            unc.append("no explicit risk-factor passages retrieved; "
                       "filings may phrase risks differently")
            for ev in evidence[:3]:
                for kp in ev["key_points"][:1]:
                    findings.append(f"{kp} {ev['citation']}")
        recommendations.append({
            "action": "Map each disclosed risk to a mitigation owner and a "
                      "monitoring metric before committing to the vendor",
            "why": "SEC risk factors are management's own statement of what "
                   "could hurt the business",
            "evidence": [e["citation"] for e in evidence[:3]],
            "kind": "confirmed practice",
            "expected_impact": "fewer unpriced vendor risks in the contract",
            "how_to_measure": "share of disclosed risks with a named mitigation",
        })
        return {"agent": self.name, "evidence": evidence, "findings": findings,
                "recommendations": recommendations, "confidence": conf,
                "uncertainties": unc}


class CSRAgent(DomainAgent):
    domain = "csr"

    def analyze(self, query):
        evidence = self.gather(query, k=5)
        conf, unc = self.confidence_of(evidence)
        findings, recommendations = [], []
        for ev in evidence[:3]:
            for kp in ev["key_points"][:2]:
                findings.append(f"{kp} {ev['citation']}")
        recommendations.append({
            "action": "Prioritize technology investments that digitize the "
                      "agrifood supply chain (traceability, demand forecasting)",
            "why": "SOFI reports tie food insecurity to supply-chain fragility "
                   "and financing gaps",
            "evidence": [e["citation"] for e in evidence[:2]],
            "kind": "hypothesis",
            "expected_impact": "lower waste and better availability in served regions",
            "how_to_measure": "food loss percentage and on-time delivery in pilot lanes",
        })
        recommendations.append({
            "action": "Align the investment case with SOFI financing benchmarks "
                      "for hunger reduction",
            "why": "keeps ESG claims anchored to authoritative estimates",
            "evidence": [e["citation"] for e in evidence[:1]],
            "kind": "confirmed practice",
            "expected_impact": "credible, auditable sustainability reporting",
            "how_to_measure": "third-party ESG disclosure score",
        })
        return {"agent": self.name, "evidence": evidence, "findings": findings,
                "recommendations": recommendations, "confidence": conf,
                "uncertainties": unc}


def _kw_hits(ql: str, keywords):
    """Word-boundary keyword hits (plural-insensitive), avoiding substring
    false positives like 'sec' in 'ipsec' or 'stain' in 'sustainability'.
    Returns the set of matched keywords."""
    return {kw for kw in keywords
            if re.search(r"\b" + re.escape(kw) + r"s?\b", ql)}


# Bare company/vendor names mention a company without establishing that the
# question belongs to the vendor's domain (e.g. "Cisco" in an SEC question).
COMPANY_WORDS = {"cisco", "agilent", "alphabet", "ibm", "google", "hanwha",
                 "bosch", "ge", "pelco", "dahua", "honeywell", "dsc"}


class ManagerAgent:
    """Intent detection, routing, orchestration."""

    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        self.recommender = ComponentRecommender()
        self.agents = {
            "technology": TechnologyAgent(kb, self.recommender),
            "clinical": ClinicalAgent(kb),
            "sec": SECAgent(kb),
            "csr": CSRAgent(kb),
        }

    def classify(self, query):
        centroid = self.kb.domain_scores(query)
        ql = query.lower()
        scores, hits, strong_hits = {}, {}, {}
        for d in self.kb.domains:
            matched = _kw_hits(ql, DOMAIN_KEYWORDS[d])
            strong = {k for k in matched if k not in COMPANY_WORDS}
            weak = len(matched) - len(strong)
            hits[d], strong_hits[d] = len(matched), len(strong)
            # company-name mentions carry less intent weight than topical terms
            kw_score = min(1.0, (len(strong) + 0.3 * weak) / 3.0)
            scores[d] = round(0.65 * centroid.get(d, 0.0) + 0.35 * kw_score, 3)
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        top_domain, top_score = ranked[0]
        if top_score < 0.08:
            return {"domains": [], "scores": scores, "confidence": "low",
                    "ambiguous": True}
        strong_domains = [d for d in self.kb.domains if hits[d] >= 2]
        multi_intent = len(strong_domains) >= 2
        selected = [top_domain]
        for d, s in ranked[1:]:
            if d in selected:
                continue
            if hits[d] >= 2:
                selected.append(d)                       # explicitly named
            elif multi_intent and hits[d] >= 1 and s >= 0.12:
                selected.append(d)                       # secondary intent
            elif strong_hits[d] >= 1 and s >= 0.15:
                selected.append(d)                       # strong single signal
            elif (hits[d] >= 1 and strong_hits[d] >= 1
                    and s >= 0.45 * top_score and s >= 0.05):
                selected.append(d)                       # semantic backup
        margin = (ranked[0][1] - ranked[1][1]) / (ranked[0][1] + 1e-9)
        conf = "high" if margin > 0.4 else "medium" if margin > 0.15 else "low"
        return {"domains": selected, "scores": scores, "confidence": conf,
                "ambiguous": False}

    def handle(self, query):
        routing = self.classify(query)
        if routing["ambiguous"]:
            return {
                "query": query, "routing": routing,
                "clarification_needed": True,
                "message": ("I couldn't confidently route this request. "
                            "Could you specify whether this concerns network "
                            "technology, clinical diagnostics, financial/SEC "
                            "matters, or sustainability?"),
                "suggested_domains": [d for d, _ in sorted(
                    routing["scores"].items(), key=lambda x: -x[1])[:2]],
            }
        reports = [self.agents[d].analyze(query) for d in routing["domains"]]
        return self.consolidate(query, routing, reports)

    def consolidate(self, query, routing, reports):
        insights, recommendations, uncertainties, evidence = [], [], [], []
        for rep in reports:
            insights.append({"agent": rep["agent"], "points": rep["findings"]})
            recommendations.extend(
                [{**r, "from": rep["agent"]} for r in rep["recommendations"]])
            uncertainties.extend(
                [f"{rep['agent']}: {u}" for u in rep["uncertainties"]])
            evidence.extend(rep["evidence"])
        cross = len(reports) > 1
        next_actions = []
        for i, r in enumerate(recommendations[:6], 1):
            next_actions.append(
                f"{i}. [{r['from']}] {r['action']} "
                f"({'confirmed' if r['kind'] == 'confirmed practice' else 'hypothesis, verify before committing'})")
        next_actions.append(
            f"{len(next_actions) + 1}. Re-run this assessment after acting: "
            "confirm the fix worked and update the evidence base.")
        avg_conf = (sum(r["confidence"] for r in reports) / len(reports)
                    if reports else 0.0)
        business_value = (
            f"This assessment consulted {len(reports)} specialist "
            f"{'agent' if len(reports) == 1 else 'agents'} "
            f"({', '.join(r['agent'] for r in reports)}) over "
            f"{len(evidence)} cited evidence passages. "
            f"{'Cross-domain synthesis was applied because the request spans '
               'multiple business concerns.' if cross else ''} "
            f"Average agent confidence is {avg_conf:.2f}. "
            "Each recommendation states why it is appropriate and how its "
            "impact can be measured, so progress is observable rather than assumed.")
        return {
            "query": query,
            "routing": {**routing, "explanation":
                        f"Intent matched {', '.join(routing['domains'])} "
                        f"with {routing['confidence']} confidence."},
            "agent_reports": reports,
            "insights": insights,
            "recommendations": recommendations,
            "next_actions": next_actions,
            "uncertainties": uncertainties,
            "business_value": business_value.strip(),
            "overall_confidence": round(avg_conf, 2),
        }
