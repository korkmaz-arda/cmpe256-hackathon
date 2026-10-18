"""Technology agent: Principal Network & Cloud Solutions Architect (Cisco routers, Google Cloud MCP/RAG)."""
from __future__ import annotations

import json

from claude_agent_sdk import SdkMcpTool

from consultai.agents.base import Specialist, ToolContext, format_evidence, make_tool, search_and_register
from consultai.agents.technology import catalog
from consultai.contracts import inline_schema
from consultai.ingest.sources import SOURCES_BY_ID

FAMILY_ENUM = catalog.FAMILIES + ["gcp-mcp", "gcp-rag"]


class TechnologyAgent(Specialist):
    name = "technology"
    display_name = "Technology Agent"
    persona = "Principal Network & Cloud Solutions Architect"
    capability = ("Enterprise networking and cloud AI architecture. Cisco router platforms (Catalyst 8300, "
                  "Catalyst 8200, Catalyst 8000V virtual, ISR 4000, ASR 1000): specifications, orderable components "
                  "and part numbers (power supplies, network/service modules, memory, storage), compatibility, "
                  "lifecycle (end-of-sale) and platform selection/refresh. Google Cloud: MCP servers and RAG concepts. "
                  "Router failures, replacement parts, network/IT investment choices. No IBM data.")
    routing_examples = [
        "Our Cisco router keeps dropping connections; which replacement parts should we order?",
        "Which Cisco edge platform should replace our ISR 4331 branch routers?",
        "How could we use Google Cloud MCP servers and RAG to ground an AI assistant on our documents?",
    ]

    def domain_tools(self, ctx: ToolContext) -> list[SdkMcpTool]:
        reg, agent = ctx.registry, self.name

        def search_tech_docs(args: dict) -> str:
            vendor, family = args.get("vendor"), args.get("family")

            def where(c: dict) -> bool:
                m = c["meta"]
                return (not vendor or m.get("vendor", "").lower() == vendor.lower()) and \
                       (not family or m.get("family") == family)

            return search_and_register(ctx, "search_tech_docs", "tech_docs", args["query"], args.get("k", 6), where)

        def _platform_evidence(p: catalog.Platform, tool_name: str):
            src = SOURCES_BY_ID[f"cisco-{p.family}-datasheet"]
            values = "; ".join(f"{e.attribute}: '{e.value_text}' (p. {e.page})" for e in p.attribute_evidence)
            return reg.add(agent, tool=tool_name, query=p.model, source_id=src.source_id, title=src.title,
                           locator=f"p. {p.page} (+ attribute pages listed)", page=p.page, section="platform specifications",
                           citation_url=f"{src.citation_url}#page={p.page}", local_path=str(src.local_path),
                           snippet=f"{p.model}: {p.summary}\nVerified values (string found on the cited page): {values}")

        def _lifecycle_evidence(family: str, tool_name: str):
            lc = catalog.lifecycle().get(family)
            if not lc:
                return None, None
            src = SOURCES_BY_ID[lc["source_id"]]
            if lc["end_of_sale"]:
                text = f"End-of-sale date: {lc['end_of_sale']}; End-of-support date: {lc['end_of_support']}"
            else:
                text = "No end-of-sale announcement on the saved product page."
            ev = reg.add(agent, tool=tool_name, query=family, source_id=src.source_id, title=src.title,
                         locator="product page", citation_url=src.citation_url, local_path=str(src.local_path), snippet=text)
            return ev, lc

        def get_platform_specs(args: dict) -> str:
            target = (args.get("model_or_family") or "").strip()
            fam = target if target in catalog.FAMILIES else catalog.family_of_model(target)
            plats = [p for p in catalog.platforms()
                     if p.model.upper().replace(" ", "") == target.upper().replace(" ", "") or (fam and p.family == fam)]
            if not plats:
                return (f"No platform matching {target!r} in the data-sheet catalog. Catalog families: "
                        f"{', '.join(catalog.FAMILIES)}. The customer's model may not be covered by our sources.")
            out = []
            lc_ev, _ = _lifecycle_evidence(plats[0].family, "get_platform_specs")
            if lc_ev:
                out.append(format_evidence(lc_ev))
            for p in plats[:12]:
                out.append(format_evidence(_platform_evidence(p, "get_platform_specs")))
            note = ("\nAttributes not listed were not stated in the data sheet (or could not be verified); treat them "
                    "as unknown.")
            return "\n\n".join(out) + note

        def recommend_platforms(args: dict) -> str:
            req = catalog.PlatformRequirements.model_validate(args)
            res = catalog.recommend_platforms(req)
            lines = [f"Recommender weights: {json.dumps(res['weights'])}"]
            if res["baseline_family_lifecycle"]:
                ev, _ = _lifecycle_evidence(catalog.family_of_model(req.current_model), "recommend_platforms")
                if ev:
                    lines.append(f"Current model lifecycle evidence: [{ev.evidence_id}] {ev.snippet}")
            if req.current_model and not res["baseline"]:
                lines.append(f"Note: {req.current_model} has no verified spec row in the catalog; capacity of the "
                             f"current model could not be used as a floor - ask for its throughput/port needs.")
            for rank, r in enumerate(res["ranked"], 1):
                p = next(x for x in catalog.platforms() if x.model == r["model"])
                ev = _platform_evidence(p, "recommend_platforms")
                lc = r["lifecycle"] or {}
                life = f"END-OF-SALE {lc['end_of_sale']}" if lc.get("end_of_sale") else "orderable (no EoS notice in sources)"
                lines.append(f"{rank}. {r['model']} ({r['family']}) score={r['score']} components={r['components']} "
                             f"lifecycle={life} unverified={r['requirements_unverified']} evidence=[{ev.evidence_id}]\n"
                             f"   {r['summary']}")
            if res["excluded"]:
                lines.append("Excluded: " + "; ".join(f"{e['model']} ({e['reason']})" for e in res["excluded"][:12]))
            return "\n".join(lines)

        def find_components(args: dict) -> str:
            target = (args.get("model_or_family") or "").strip()
            category, text = args.get("category"), (args.get("contains") or "").lower()
            fam = target if target in catalog.FAMILIES else catalog.family_of_model(target)
            raw = catalog.load_catalog()["components"]
            comps = [catalog.Component.model_validate(c) for c in raw
                     if (not fam or c["source_id"] == f"cisco-{fam}-datasheet")
                     and (not category or c["category"] == category)
                     and (not text or text in (c["pid"] + " " + c["description"]).lower())]
            if not comps:
                return (f"No orderable components found for {target or 'any family'} / category={category} / "
                        f"contains={text!r} in the data sheets.")
            by_page: dict[tuple[str, int], list[catalog.Component]] = {}
            for c in comps:
                by_page.setdefault((fam or "", c.page), []).append(c)
            out = []
            for (_, page), items in sorted(by_page.items(), key=lambda kv: kv[0][1])[:8]:
                src = SOURCES_BY_ID[f"cisco-{fam}-datasheet"] if fam else SOURCES_BY_ID["cisco-catalyst-8300-datasheet"]
                listing = "\n".join(f"- {c.pid} [{c.category}]: {c.description}"
                                    + (f" (for: {', '.join(c.applies_to)})" if c.applies_to else "") for c in items[:25])
                ev = reg.add(agent, tool="find_components", query=f"{target} {category or ''} {text}".strip(),
                             source_id=src.source_id, title=src.title, locator=f"p. {page}", page=page,
                             section="orderable components", citation_url=f"{src.citation_url}#page={page}",
                             local_path=str(src.local_path), snippet=f"Part numbers verified on p. {page}:\n{listing}")
                out.append(format_evidence(ev))
            return "\n\n".join(out)

        return [
            make_tool(ctx, "search_tech_docs",
                      "Hybrid search over the Cisco data sheets / product pages and the Google Cloud MCP & RAG pages. "
                      "Optional filters: vendor ('Cisco' or 'Google'), family (" + ", ".join(FAMILY_ENUM) + "). "
                      "Returns passages with evidence ids, page numbers and retrieval scores.",
                      {"type": "object", "properties": {
                          "query": {"type": "string"}, "vendor": {"type": "string", "enum": ["Cisco", "Google"]},
                          "family": {"type": "string", "enum": FAMILY_ENUM}, "k": {"type": "integer", "minimum": 1, "maximum": 10}},
                       "required": ["query"]}, search_tech_docs),
            make_tool(ctx, "get_platform_specs",
                      "Verified specifications of a Cisco platform model (e.g. C8300-1N1S-6T, ISR4331, ASR1001-X) or a whole "
                      "family (catalyst-8300, catalyst-8200, catalyst-8000v, isr-4000, asr-1000), plus the family's "
                      "lifecycle status (end-of-sale / end-of-support) from its product page.",
                      {"type": "object", "properties": {"model_or_family": {"type": "string"}}, "required": ["model_or_family"]},
                      get_platform_specs),
            make_tool(ctx, "recommend_platforms",
                      "Content-based platform recommender. Filters by hard constraints, then ranks by requirement fit "
                      "(verified data-sheet values), similarity of the use case to each platform, deployment context and a "
                      "lifecycle penalty for end-of-sale families. Returns ranked models with score components, "
                      "exclusions with reasons, and evidence ids.",
                      inline_schema(catalog.PlatformRequirements), recommend_platforms),
            make_tool(ctx, "find_components",
                      "List orderable part numbers from a family's data sheet (verified on the cited page). Filters: "
                      "model_or_family, category (power_supply, network_module, service_module, memory, storage, license, "
                      "route_processor, embedded_services_processor, accessory), contains (text).",
                      {"type": "object", "properties": {
                          "model_or_family": {"type": "string"}, "category": {"type": "string"},
                          "contains": {"type": "string"}}, "required": ["model_or_family"]}, find_components),
        ]
