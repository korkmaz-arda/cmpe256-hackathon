"""Corporate Responsibility agent: Sustainability & Food-Systems Strategy Advisor (FAO SOFI 2023 and 2024)."""
from __future__ import annotations

from claude_agent_sdk import SdkMcpTool

from consultai.agents.base import Specialist, ToolContext, make_tool, search_and_register


class CSRAgent(Specialist):
    name = "csr"
    display_name = "Corporate Responsibility Agent"
    persona = "Sustainability & Food-Systems Strategy Advisor"
    capability = ("Corporate social responsibility, ESG and sustainability strategy with a focus on food security "
                  "and nutrition, grounded in the UN/FAO State of Food Security and Nutrition in the World reports "
                  "(SOFI 2023: urbanization and agrifood systems; SOFI 2024: financing to end hunger): hunger and food "
                  "insecurity levels and drivers (conflict, climate extremes, economic downturns, food prices), "
                  "malnutrition, healthy-diet affordability, financing and investment levers, impact indicators.")
    routing_examples = [
        "List the major reasons for food insecurity in 2024.",
        "Explain malnutrition in war zones.",
        "Which technology investments could improve food security and sustainability outcomes?",
    ]

    def domain_tools(self, ctx: ToolContext) -> list[SdkMcpTool]:
        def search_sofi(args: dict) -> str:
            edition = args.get("edition")
            return search_and_register(ctx, "search_sofi", "sofi", args["query"], args.get("k", 6),
                                       (lambda c: c["meta"].get("edition") == edition) if edition else None,
                                       extra=lambda c: f" | SOFI {c['meta']['edition']}")

        return [
            make_tool(ctx, "search_sofi",
                      "Search the SOFI 2023 and SOFI 2024 reports (FAO, IFAD, UNICEF, WFP, WHO). Optional edition filter "
                      "(2023 or 2024). Results show edition, chapter and PDF page.",
                      {"type": "object", "properties": {"query": {"type": "string"},
                                                        "edition": {"type": "integer", "enum": [2023, 2024]},
                                                        "k": {"type": "integer", "minimum": 1, "maximum": 10}},
                       "required": ["query"]}, search_sofi),
        ]
