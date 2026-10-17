"""Render a ManagerAgent result as Markdown (used by the CLI, the demo transcripts and the UI)."""
from __future__ import annotations

from app import config

PREFIX = {"technology": "TECH", "clinical": "CLIN", "sec": "SEC", "csr": "CSR"}


def _cite(ids: list[str]) -> str:
    return f" [{', '.join(ids)}]" if ids else ""


def source_label(s: dict) -> str:
    page = f", p.{s['page']}" if s.get("page") else ""
    link = f" <{s['url']}>" if s.get("url") else (f" `{s['path']}`" if s.get("path") else "")
    return f"{s['title']}{page}{link}"


def answer_markdown(ans: dict) -> str:
    lines = [ans["summary"], ""]
    if ans.get("findings"):
        lines.append("**Findings**")
        for f in ans["findings"]:
            tag = "✅ confirmed" if f["status"] == "confirmed" else "🔍 hypothesis"
            lines.append(f"- ({tag}) {f['claim']}{_cite(f['sources'])}")
        lines.append("")
    if ans.get("recommendations"):
        lines.append("**Recommendations**")
        for r in ans["recommendations"]:
            lines.append(f"- **[{r['priority']}] {r['action']}**: {r['why']}{_cite(r['sources'])}")
        lines.append("")
    for key, title in (("next_steps", "Next steps"), ("missing_information", "Information needed from you"),
                       ("risks_assumptions", "Risks and assumptions")):
        if ans.get(key):
            lines.append(f"**{title}**")
            lines += [f"- {x}" for x in ans[key]]
            lines.append("")
    if ans.get("kpis"):
        lines.append("**How to measure impact (KPIs)**")
        lines += [f"- {k['metric']}: {k['how_to_measure']}" for k in ans["kpis"]]
        lines.append("")
    c = ans.get("confidence", {})
    lines.append(f"**Confidence:** {c.get('level', '?')}: {c.get('reason', '')}")
    return "\n".join(lines)


def synthesis_markdown(syn: dict) -> str:
    lines = [syn["executive_summary"], "", "**Integrated recommendations**"]
    for r in syn["integrated_recommendations"]:
        lines.append(f"- **[{r['priority']}] {r['action']}**: {r['why']}{_cite(r['sources'])}")
    for key, title in (("cross_domain_links", "How the domains connect"), ("conflicts_or_gaps", "Conflicts and gaps"),
                       ("next_steps", "Next steps")):
        if syn.get(key):
            lines += ["", f"**{title}**"] + [f"- {x}" for x in syn[key]]
    if syn.get("kpis"):
        lines += ["", "**How to measure impact (KPIs)**"] + [f"- {k['metric']}: {k['how_to_measure']}" for k in syn["kpis"]]
    c = syn.get("confidence", {})
    lines += ["", f"**Confidence:** {c.get('level', '?')}: {c.get('reason', '')}"]
    return "\n".join(lines)


def to_markdown(result: dict) -> str:
    r = result["route"]
    lines = [f"## Q: {result['query']}", "",
             f"**Route** ({r['model']}, {r['seconds']}s): {', '.join(r['routes'])}"
             f"{' (cross-domain)' if r.get('cross_domain') else ''}: {r['reason']} (confidence {r['confidence']:.2f})", ""]
    if r["routes"] == ["out_of_scope"]:
        lines.append("This request is outside our four practice areas (technology, clinical, SEC filings, "
                     "food security / CSR), so no specialist was engaged.")
        return "\n".join(lines)
    if result.get("synthesis"):
        lines += ["### Consolidated consulting recommendation (Manager Agent)", "", synthesis_markdown(result["synthesis"]), ""]
    for domain, res in result["agents"].items():
        g = res["grounding"]
        lines += [f"### {res['agent']} ({res['seconds']}s)", f"*Sub-question:* {res['question']}", "",
                  answer_markdown(res["answer"]), "",
                  f"*Grounding:* {g['sources_retrieved']} sources, {g['confirmed']} confirmed / {g['hypotheses']} hypotheses, "
                  f"citation coverage {g['citation_coverage']:.0%}, grounding score {g['grounding_score']:.2f}",
                  f"*Tools used:* " + ", ".join(f"`{t['tool']}`" for t in res["tool_calls"]), ""]
        cited = {s for item in res["answer"].get("findings", []) + res["answer"].get("recommendations", [])
                 for s in item.get("sources", [])}
        prefix = f"{PREFIX[domain]}-" if result.get("synthesis") else ""
        refs = [f"- **{prefix}{s['id']}**: {source_label(s)}" for s in res["sources"] if s["id"] in cited]
        if refs:
            lines += ["**Sources cited**"] + refs + [""]
    lines.append(f"*Total time: {result.get('seconds')}s*")
    return "\n".join(lines)
