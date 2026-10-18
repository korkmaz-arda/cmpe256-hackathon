"""SEC agent: Equity Research & Regulatory-Risk Analyst (Form 10-K filings of Agilent, Alphabet and Cisco)."""
from __future__ import annotations

import ast
import operator

from claude_agent_sdk import SdkMcpTool

from consultai.agents.base import Specialist, ToolContext, make_tool, search_and_register
from consultai.ingest.sources import SEC_SOURCES

COMPANIES = sorted({s.meta["company"] for s in SEC_SOURCES})
ITEMS = ["1", "1A", "1B", "1C", "2", "3", "5", "7", "7A", "8", "9A", "10", "11"]

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}


def safe_eval(expr: str) -> float:
    """Arithmetic only (numbers, + - * / ** and parentheses); no names, calls or attributes."""
    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError("only numbers and + - * / ** ( ) are allowed")
    return ev(ast.parse(expr.replace(",", ""), mode="eval"))


class SECAgent(Specialist):
    name = "sec"
    display_name = "SEC Agent"
    persona = "Equity Research & Regulatory-Risk Analyst"
    capability = ("Financial, competitive, operational and regulatory analysis of Cisco, Agilent and Alphabet (Google) "
                  "from their Form 10-K annual reports (Cisco FY2025 & FY2026, Agilent FY2025, Alphabet FY2024 & FY2025): "
                  "revenue and segment trends, margins, risk factors, supply chain, legal/regulatory exposure, "
                  "acquisitions, cybersecurity governance, climate/sustainability disclosures; vendor and partner risk.")
    routing_examples = [
        "What are the financial, competitive and operational risks associated with Cisco and Agilent?",
        "How did Google Cloud revenue develop according to Alphabet's latest annual report?",
        "Is Cisco a financially stable long-term vendor for our network refresh?",
    ]

    def domain_tools(self, ctx: ToolContext) -> list[SdkMcpTool]:
        def list_filings(_args: dict) -> str:
            rows = [f"- `{s.source_id}`: {s.meta['company']} Form 10-K, fiscal year {s.meta['fiscal_year']} "
                    f"(ended {s.meta['fiscal_year_end']}), accession {s.meta['accession']}" for s in SEC_SOURCES]
            return ("Filings in the knowledge base (fiscal years end on different dates: Agilent Oct 31, "
                    "Alphabet Dec 31, Cisco late July):\n" + "\n".join(rows))

        def search_filings(args: dict) -> str:
            companies = {c.lower() for c in args.get("companies") or []}
            years = set(args.get("fiscal_years") or [])
            items = [f"Item {i.upper()}." for i in args.get("items") or []]

            def where(c: dict) -> bool:
                m = c["meta"]
                return ((not companies or m["company"].lower() in companies)
                        and (not years or m["fiscal_year"] in years)
                        and (not items or any((c.get("section") or "").startswith(i) for i in items)))

            return search_and_register(ctx, "search_filings", "sec_filings", args["query"], args.get("k", 6), where,
                                       extra=lambda c: f" | {c['meta']['company']} FY{c['meta']['fiscal_year']}")

        def calc(args: dict) -> str:
            value = safe_eval(args["expression"])
            return f"{args['expression']} = {value:,.4f}" + (f"  ({args['label']})" if args.get("label") else "")

        return [
            make_tool(ctx, "list_filings", "List the 10-K filings available (company, fiscal year, period end, accession).",
                      {"type": "object", "properties": {}}, list_filings),
            make_tool(ctx, "search_filings",
                      "Search the 10-K filings. Filters: companies (" + ", ".join(COMPANIES) + "), fiscal_years "
                      "(e.g. [2025]), items (10-K Item numbers, e.g. ['1A'] risk factors, ['7'] MD&A, ['8'] financial "
                      "statements, ['1C'] cybersecurity, ['1'] business). Results show company, fiscal year, Item and page.",
                      {"type": "object", "properties": {
                          "query": {"type": "string"},
                          "companies": {"type": "array", "items": {"type": "string", "enum": COMPANIES}},
                          "fiscal_years": {"type": "array", "items": {"type": "integer"}},
                          "items": {"type": "array", "items": {"type": "string", "enum": ITEMS}},
                          "k": {"type": "integer", "minimum": 1, "maximum": 10}}, "required": ["query"]}, search_filings),
            make_tool(ctx, "calc",
                      "Exact arithmetic for derived figures (growth rates, margins, ratios). Use numbers exactly as "
                      "quoted from cited evidence, e.g. expression '(56654-53803)/53803*100', label 'revenue growth %'.",
                      {"type": "object", "properties": {"expression": {"type": "string"}, "label": {"type": "string"}},
                       "required": ["expression"]}, calc, counts_against_budget=False),
        ]
