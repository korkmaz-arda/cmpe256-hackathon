"""Clinical agent: Clinical & Life-Science Solutions Consultant (Agilent products, clinical literature, trial registry)."""
from __future__ import annotations

import json

from claude_agent_sdk import SdkMcpTool

from consultai.agents.base import Specialist, ToolContext, format_evidence, make_tool, search_and_register
from consultai.agents.clinical import agilent_catalog
from consultai.contracts import inline_schema
from consultai.ingest import trials as trials_db
from consultai.ingest.sources import SOURCES_BY_ID, TRIAL_SETS
from consultai.retrieval.store import collection

TOPICS = ["covid", "diabetes", "heart_attack", "knee_injuries"]
STATUSES = ["COMPLETED", "RECRUITING", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION",
            "TERMINATED", "WITHDRAWN", "SUSPENDED", "UNKNOWN"]
GROUP_BY = {"status": "t.status", "phase": "t.phases", "study_type": "t.study_type", "funder_type": "t.funder_type",
            "start_year": "t.start_year", "sponsor": "t.sponsor", "has_results": "t.has_results"}


class ClinicalAgent(Specialist):
    name = "clinical"
    display_name = "Clinical Agent"
    persona = "Clinical & Life-Science Solutions Consultant"
    capability = ("Healthcare, medical diagnostics and life-science labs. Agilent instruments for digital pathology "
                  "(NanoZoomer S360MD IVD scanner, S540MD, image management, AI apps), special staining (Artisan Link Pro) "
                  "and cell metabolic analysis (Seahorse XF); which instrument fits a lab's requirements. Clinical evidence "
                  "on COVID-19, diabetes, heart attack and knee injuries from IEEE papers and 32k ClinicalTrials.gov "
                  "studies (trial landscape, counts, sponsors, phases).")
    routing_examples = [
        "Which diagnostic instrument best meets our pathology lab's requirements for primary diagnosis?",
        "What does the clinical trial landscape for continuous glucose monitoring in type 1 diabetes look like?",
        "What machine-learning approaches have been used to predict heart attacks?",
    ]

    def domain_tools(self, ctx: ToolContext) -> list[SdkMcpTool]:
        reg, agent = ctx.registry, self.name

        def search_agilent(args: dict) -> str:
            return search_and_register(ctx, "search_agilent", "agilent", args["query"], args.get("k", 5))

        def recommend_agilent_products(args: dict) -> str:
            req = agilent_catalog.LabRequirements.model_validate(args)
            res = agilent_catalog.recommend_agilent_products(req)
            lines = [f"Recommender weights: {json.dumps(res['weights'])}"]
            for rank, r in enumerate(res["ranked"], 1):
                src = SOURCES_BY_ID[r["source_id"]]
                specs = "\n".join(f"  - {s}" for s in r["specs"])
                ev = reg.add(agent, tool="recommend_agilent_products", query=req.need, source_id=src.source_id,
                             title=src.title, locator="web page", citation_url=src.citation_url,
                             local_path=str(src.local_path),
                             snippet=f"{r['product']} (regulatory status on page: {r['regulatory_status']}; part numbers: "
                                     f"{', '.join(r['part_numbers']) or 'none listed'})\n{r['summary']}\n{specs}")
                lines.append(f"{rank}. {r['product']} score={r['score']} components={r['components']} "
                             f"status={r['regulatory_status']} evidence=[{ev.evidence_id}]")
            if res["excluded"]:
                lines.append("Excluded: " + "; ".join(f"{e['product']} ({e['reason']})" for e in res["excluded"]))
            return "\n".join(lines)

        def search_literature(args: dict) -> str:
            topic = args.get("topic")
            return search_and_register(ctx, "search_literature", "clinical_lit", args["query"], args.get("k", 6),
                                       (lambda c: c["meta"].get("topic") == topic) if topic else None)

        def search_trials(args: dict) -> str:
            cset, status, phase = args.get("condition_set"), args.get("status"), args.get("phase")
            stype, has_results = args.get("study_type"), args.get("has_results")

            def where(c: dict) -> bool:
                m = c["meta"]
                return ((not cset or cset in m["condition_sets"]) and (not status or m["status"] == status)
                        and (not phase or phase in (m["phases"] or "")) and (not stype or m["study_type"] == stype)
                        and (has_results is None or m["has_results"] == has_results))

            hits = collection("trials").search(args["query"], k=max(1, min(int(args.get("k", 8)), 10)), where=where)
            if not hits:
                return "No trials match this query and these filters."
            out = []
            for h in hits:
                m = h.chunk["meta"]
                ev = reg.add(agent, tool="search_trials", query=args["query"], source_id=h.chunk["source_id"],
                             title=f"ClinicalTrials.gov {m['nct_id']}", locator=m["nct_id"], citation_url=m["url"],
                             local_path=str(SOURCES_BY_ID[h.chunk["source_id"]].local_path),
                             snippet=h.chunk["text"][:900], scores=h.scores)
                out.append(format_evidence(ev, f" | enrollment {m['enrollment']} | start {m['start_year']} | "
                                               f"results posted: {m['has_results']}"))
            return f"{len(hits)} trials (hybrid retrieval + rerank over trial cards):\n\n" + "\n\n".join(out)

        def trial_stats(args: dict) -> str:
            group = args.get("group_by", "status")
            if group not in GROUP_BY:
                return f"group_by must be one of {list(GROUP_BY)}"
            where, params = ["1=1"], []
            if args.get("condition_set"):
                where.append("s.condition_set = ?")
                params.append(args["condition_set"])
            if args.get("status"):
                where.append("t.status = ?")
                params.append(args["status"])
            if args.get("study_type"):
                where.append("t.study_type = ?")
                params.append(args["study_type"])
            if args.get("contains"):
                where.append("(t.title || ' ' || t.conditions || ' ' || t.interventions) LIKE ?")
                params.append(f"%{args['contains']}%")
            sql = (f"SELECT {GROUP_BY[group]} AS grp, COUNT(DISTINCT t.nct_id) AS n FROM trials t "
                   f"JOIN trial_sets s ON s.nct_id = t.nct_id WHERE {' AND '.join(where)} GROUP BY grp ORDER BY n DESC LIMIT 15")
            total_sql = (f"SELECT COUNT(DISTINCT t.nct_id) FROM trials t JOIN trial_sets s ON s.nct_id = t.nct_id "
                         f"WHERE {' AND '.join(where)}")
            con = trials_db.connect()
            rows = con.execute(sql, params).fetchall()
            total = con.execute(total_sql, params).fetchone()[0]
            table = "\n".join(f"  {r['grp'] or '(blank)'}: {r['n']}" for r in rows)
            cset = args.get("condition_set")
            src = SOURCES_BY_ID[f"ctg-{cset}"] if cset else SOURCES_BY_ID["ctg-diabetes"]
            ev = reg.add(agent, tool="trial_stats", query=json.dumps(args), source_id=src.source_id,
                         title=(src.title if cset else "ClinicalTrials.gov exports (all four condition sets)"),
                         locator=f"registry query (group by {group})", citation_url="https://clinicaltrials.gov",
                         local_path=str(src.local_path),
                         snippet=f"Exact SQL count over the registry export. Filters: {json.dumps(args)}\n"
                                 f"Total matching trials: {total}\nBy {group} (top 15):\n{table}")
            return format_evidence(ev)

        return [
            make_tool(ctx, "search_agilent",
                      "Search the six Agilent web pages (digital pathology, NanoZoomer scanners, Artisan Link Pro special "
                      "stains, Seahorse XF cell metabolic analysis, 2023 award press release).",
                      {"type": "object", "properties": {"query": {"type": "string"}, "k": {"type": "integer"}},
                       "required": ["query"]}, search_agilent),
            make_tool(ctx, "recommend_agilent_products",
                      "Rank Agilent products for a lab requirement: excludes research-use-only products when the use is "
                      "clinical diagnosis, then ranks by similarity to the need and application overlap. Returns score "
                      "components and evidence ids.",
                      inline_schema(agilent_catalog.LabRequirements), recommend_agilent_products),
            make_tool(ctx, "search_literature",
                      "Search the 20 IEEE papers (5 each: covid, diabetes, heart_attack, knee_injuries). Optional topic filter.",
                      {"type": "object", "properties": {"query": {"type": "string"},
                                                        "topic": {"type": "string", "enum": TOPICS},
                                                        "k": {"type": "integer"}}, "required": ["query"]}, search_literature),
            make_tool(ctx, "search_trials",
                      "Find relevant trials in the ClinicalTrials.gov exports (32k unique studies). Filters: condition_set "
                      f"({', '.join(TRIAL_SETS)}), status, phase (e.g. PHASE3), study_type (INTERVENTIONAL/OBSERVATIONAL), "
                      "has_results. Returns NCT ids with links.",
                      {"type": "object", "properties": {
                          "query": {"type": "string"}, "condition_set": {"type": "string", "enum": list(TRIAL_SETS)},
                          "status": {"type": "string", "enum": STATUSES}, "phase": {"type": "string"},
                          "study_type": {"type": "string", "enum": ["INTERVENTIONAL", "OBSERVATIONAL", "EXPANDED_ACCESS"]},
                          "has_results": {"type": "boolean"}, "k": {"type": "integer"}}, "required": ["query"]}, search_trials),
            make_tool(ctx, "trial_stats",
                      "Exact counts from the trial registry via SQL (never estimate counts yourself). Filters: condition_set, "
                      "status, study_type, contains (text in title/conditions/interventions). group_by: "
                      + ", ".join(GROUP_BY) + ".",
                      {"type": "object", "properties": {
                          "condition_set": {"type": "string", "enum": list(TRIAL_SETS)},
                          "status": {"type": "string", "enum": STATUSES},
                          "study_type": {"type": "string", "enum": ["INTERVENTIONAL", "OBSERVATIONAL", "EXPANDED_ACCESS"]},
                          "contains": {"type": "string"}, "group_by": {"type": "string", "enum": list(GROUP_BY)}},
                       "required": ["group_by"]}, trial_stats),
        ]
