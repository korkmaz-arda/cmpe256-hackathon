"""Demo runner: the professor's prompt list from the Oct 17 meetings.

Prints every agent's prompt/instruction set first (persona, do/don't,
expertise, grounding), then runs prompts -> responses for:
  - 4 Food Security prompts (SOFI 2023 / 2024)
  - 1 prompt per specialist (Technology, Clinical, SEC, CSR)
  - 1 cross-domain query (Technology + SEC + CSR)
  - 1 clinical trial-grounded case (Seahorse XF / diabetes / mitochondrial)
  - 1 ambiguous query (uncertainty handling)

Saves the full consulting output to results/demo_output.txt
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retrieval import KnowledgeBase
from agents import ManagerAgent, AGENT_PROMPTS, format_prompt

RESULTS = Path(__file__).resolve().parent.parent / "results"

QUERIES = [
    ("food security / SOFI 2023",
     "List major Food insecurity reason in 2023 from within the context of "
     "State of Food Security and Nutrition in the World 2023 report."),
    ("food security / SOFI 2023",
     "Explain malnutrition in war zones, based on the State of Food Security "
     "and Nutrition in the World 2023 report."),
    ("food security / SOFI 2024",
     "List major Food insecurity reason in 2024 from within the context of "
     "State of Food Security and Nutrition in the World 2024 report."),
    ("food security / prices",
     "Explain increase prices impact on food security."),
    ("technology",
     "Which replacement components should we order to resolve a Cisco router "
     "failure?"),
    ("clinical",
     "Which diagnostic instrument or replacement component best meets our "
     "laboratory requirements?"),
    ("clinical / trial-grounded",
     "We need to measure mitochondrial function in a diabetes study. Which "
     "instrument do you recommend, and what trial evidence supports it?"),
    ("sec",
     "What are the financial, competitive, and operational risks associated "
     "with these companies?"),
    ("corporate responsibility",
     "Which technology investments could improve food security and "
     "sustainability outcomes?"),
    ("cross-domain",
     "We're considering Cisco Catalyst edge routers to monitor cold-chain "
     "food distribution. Which model fits, what risks does Cisco's 10-K "
     "disclose, and how would this support food-security outcomes per "
     "SOFI 2024?"),
    ("ambiguous / uncertainty handling",
     "Our system is down, what should we do?"),
]


def render(res) -> str:
    L = []
    L.append("=" * 78)
    L.append(f"CUSTOMER REQUEST: {res['query']}")
    L.append("=" * 78)
    if res.get("clarification_needed"):
        L.append("")
        L.append("ROUTING: ambiguous (low confidence)")
        L.append(f"MANAGER: {res['message']}")
        L.append(f"Suggested domains: {', '.join(res['suggested_domains'])}")
        return "\n".join(L)
    r = res["routing"]
    L.append("")
    L.append(f"ROUTING -> {', '.join(r['domains'])} "
             f"(confidence: {r['confidence']})")
    L.append(f"  scores: {', '.join(f'{d}={s}' for d, s in r['scores'].items())}")
    L.append("")
    L.append("EVIDENCE & INSIGHTS")
    for ins in res["insights"]:
        L.append(f"  [{ins['agent']}]")
        for p in ins["points"][:4]:
            L.append(f"    - {p}")
    L.append("")
    L.append("RECOMMENDATIONS")
    for rec in res["recommendations"]:
        L.append(f"  [{rec['from']}] {rec['action']}")
        L.append(f"    Why: {rec['why']}")
        L.append(f"    Impact: {rec['expected_impact']}")
        L.append(f"    Measure: {rec['how_to_measure']}")
    L.append("")
    L.append("NEXT ACTIONS")
    for a in res["next_actions"]:
        L.append(f"  {a}")
    L.append("")
    L.append("CONFIDENCE & UNCERTAINTIES")
    L.append(f"  Overall confidence: {res['overall_confidence']}")
    for u in res["uncertainties"]:
        L.append(f"  ! {u}")
    if not res["uncertainties"]:
        L.append("  (none flagged)")
    L.append("")
    L.append("BUSINESS VALUE")
    L.append(f"  {res['business_value']}")
    return "\n".join(L)


def main():
    kb = KnowledgeBase()
    mgr = ManagerAgent(kb)
    out = ["### AGENT PROMPTS & GROUNDING (shown per the Oct 17 rubric)", ""]
    for domain in ["manager", "technology", "clinical", "sec", "csr"]:
        out.append(format_prompt(domain))
        out.append("")
    for label, q in QUERIES:
        out.append(f"\n### DEMO CASE: {label}\n")
        out.append(render(mgr.handle(q)))
    text = "\n".join(out)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "demo_output.txt").write_text(text, encoding="utf-8")
    print(text[:4000])
    print("\n... full output saved to results/demo_output.txt")


if __name__ == "__main__":
    main()
