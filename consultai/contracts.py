"""Inter-agent contracts: every message between the manager and the specialists.

All hand-offs are these Pydantic models, validated at each boundary and written to the run trace
in full, so the interaction is lossless and auditable:

  customer request
    -> RoutingDecision          (router: which specialists, what each must answer, dependencies)
    -> SpecialistTask           (the ONLY input a specialist receives)
    <- SpecialistReport         (findings + recommendations, each tied to Evidence ids)
    -> ReviewDecision           (manager's progress ledger: goal met? gaps? conflicts? follow-ups?)
    -> ConsultingResponse       (manager's synthesis; every claim cites evidence ids)

Evidence objects are created by retrieval tool code, never by a language model. Evidence ids carry
the producing agent's prefix (TECH-3, CLIN-7, SEC-2, CSR-5), so every claim in the final answer can
be attributed to an agent and a source location.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AgentName = Literal["technology", "clinical", "sec", "csr"]
AGENT_NAMES: tuple[str, ...] = ("technology", "clinical", "sec", "csr")
EVIDENCE_PREFIX = {"technology": "TECH", "clinical": "CLIN", "sec": "SEC", "csr": "CSR"}
PREFIX_AGENT = {v: k for k, v in EVIDENCE_PREFIX.items()}

Basis = Literal["confirmed", "inferred", "general_knowledge"]
Confidence = Literal["high", "medium", "low"]
Priority = Literal["high", "medium", "low"]


def agent_of_evidence(evidence_id: str) -> str | None:
    return PREFIX_AGENT.get(evidence_id.split("-", 1)[0])


# ----------------------------------------------------------------------------- routing
class Entities(BaseModel):
    products: list[str] = Field(default_factory=list, description="Product names / models / part numbers mentioned")
    companies: list[str] = Field(default_factory=list)
    fiscal_years: list[int] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list, description="Medical conditions / clinical areas")
    regions: list[str] = Field(default_factory=list)
    other: list[str] = Field(default_factory=list, description="Other facts given by the customer (symptoms, constraints, numbers)")


class Assignment(BaseModel):
    agent: AgentName
    relevance: float = Field(ge=0, le=1, description="How central this domain is to the request (0-1)")
    rationale: str = Field(description="Why this specialist is needed")
    sub_question: str = Field(description="The precise question this specialist must answer")
    entities: Entities = Field(default_factory=Entities)
    expected_outputs: list[str] = Field(default_factory=list, description="What the manager needs back")
    depends_on: list[AgentName] = Field(default_factory=list,
                                        description="Specialists whose findings this one needs first (usually empty)")


class RoutingDecision(BaseModel):
    intents: list[str] = Field(description="Short labels of what the customer wants")
    assignments: list[Assignment] = Field(default_factory=list)
    facts_given: list[str] = Field(default_factory=list, description="Facts stated by the customer (task ledger)")
    facts_to_look_up: list[str] = Field(default_factory=list, description="Facts the specialists must establish (task ledger)")
    out_of_scope: list[str] = Field(default_factory=list, description="Parts of the request no specialist/source covers")
    clarifying_questions: list[str] = Field(default_factory=list)
    blocking: bool = Field(default=False, description="True only if the request cannot be routed without an answer from the customer")
    router: str = Field(default="llm", description="llm | knn-fallback (set by code)")


# ----------------------------------------------------------------------------- evidence
class Evidence(BaseModel):
    evidence_id: str
    agent: AgentName
    tool: str
    query: str | None = None
    source_id: str
    title: str
    locator: str = Field(description="Where in the source: 'p. 17', 'Item 1A, p. 14', 'section: ...', 'NCT01234567'")
    page: int | None = None
    section: str | None = None
    citation_url: str | None = None
    local_path: str | None = None
    snippet: str
    scores: dict[str, float] = Field(default_factory=dict)


# ----------------------------------------------------------------------------- specialist I/O
class Finding(BaseModel):
    claim: str
    basis: Basis = Field(description="confirmed = stated in the cited evidence; inferred = reasoned from it; "
                                     "general_knowledge = not from the knowledge base (must be flagged)")
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: Confidence
    confidence_reason: str


class RankedItem(BaseModel):
    item: str
    score: float | None = None
    why: str
    evidence_ids: list[str] = Field(default_factory=list)


class SpecialistRecommendation(BaseModel):
    action: str
    rationale: str
    priority: Priority
    ranked_items: list[RankedItem] = Field(default_factory=list, description="Ranked options from recommender tools, if used")
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: Confidence
    kpi: str | None = Field(default=None, description="How the customer can measure the impact")


class UpstreamContext(BaseModel):
    """Findings of another specialist that this task depends on (passed losslessly)."""
    agent: AgentName
    task_id: str
    status: str
    answer_summary: str
    findings: list[Finding] = Field(default_factory=list)
    recommendations: list[SpecialistRecommendation] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class SpecialistTask(BaseModel):
    task_id: str
    run_id: str
    agent: AgentName
    round: int = 1
    customer_request: str = Field(description="Verbatim customer request")
    conversation_context: str | None = Field(default=None, description="Earlier turns, if the customer is following up")
    objective: str
    entities: Entities = Field(default_factory=Entities)
    constraints: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    upstream: list[UpstreamContext] = Field(default_factory=list)
    follow_up_reason: str | None = None
    budget_tool_calls: int = 12


class ReportBody(BaseModel):
    """What a specialist submits through its `submit_report` tool."""
    status: Literal["ok", "partial", "insufficient_evidence", "out_of_scope"]
    answer_summary: str = Field(description="3-6 sentence answer to the objective, with [ID] citations")
    findings: list[Finding] = Field(default_factory=list)
    recommendations: list[SpecialistRecommendation] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list, description="Questions the customer must answer")
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    sources_searched: list[str] = Field(default_factory=list, description="Which tools/sources were searched, incl. dead ends")


class SpecialistReport(ReportBody):
    status: Literal["ok", "partial", "insufficient_evidence", "out_of_scope", "failed"]
    task_id: str
    agent: AgentName
    round: int = 1
    evidence: list[Evidence] = Field(default_factory=list, description="Evidence cited in this report (attached by code)")
    retrieved_evidence_count: int = 0
    tool_calls: int = 0
    error: str | None = None
    raw_text: str | None = None
    model: str | None = None
    duration_s: float | None = None
    usage: dict = Field(default_factory=dict)


# ----------------------------------------------------------------------------- manager review
class TaskAssessment(BaseModel):
    task_id: str
    agent: AgentName
    answered: bool
    gaps: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list, description="Unsupported claims, mixed fiscal years, missing citations, ...")


class Conflict(BaseModel):
    agents: list[AgentName]
    description: str
    evidence_ids: list[str] = Field(default_factory=list)


class FollowUp(BaseModel):
    agent: AgentName
    objective: str
    reason: str


class ReviewDecision(BaseModel):
    assessments: list[TaskAssessment] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    goal_met: bool
    follow_ups: list[FollowUp] = Field(default_factory=list)
    rationale: str


# ----------------------------------------------------------------------------- final answer
class ConsultingRecommendation(BaseModel):
    action: str
    why: str
    priority: Priority
    owner_agents: list[AgentName]
    evidence_ids: list[str] = Field(default_factory=list)
    basis: Basis
    confidence: Confidence


class CrossDomainInsight(BaseModel):
    insight: str
    agents: list[AgentName] = Field(description="At least two agents whose findings are combined")
    evidence_ids: list[str] = Field(default_factory=list)


class ConflictResolution(BaseModel):
    agents: list[AgentName]
    description: str
    resolution: str
    basis: str


class AttributedClaim(BaseModel):
    statement: str
    agent: AgentName
    evidence_ids: list[str] = Field(default_factory=list)


class NextStep(BaseModel):
    step: str
    owner: str = Field(description="Who at the customer should do it")
    timeframe: str


class ImpactMetric(BaseModel):
    kpi: str
    measurement: str = Field(description="How to measure it")
    baseline_source: str = Field(description="Where the baseline comes from (cited evidence or customer data to collect)")
    target: str


class ConsultingResponse(BaseModel):
    executive_summary: str
    answer: str = Field(description="Consultant's answer in markdown with [ID] citations")
    recommendations: list[ConsultingRecommendation] = Field(default_factory=list)
    cross_domain_insights: list[CrossDomainInsight] = Field(default_factory=list)
    conflicts: list[ConflictResolution] = Field(default_factory=list)
    confirmed: list[AttributedClaim] = Field(default_factory=list)
    hypotheses: list[AttributedClaim] = Field(default_factory=list)
    questions_for_customer: list[str] = Field(default_factory=list)
    next_steps: list[NextStep] = Field(default_factory=list)
    impact_metrics: list[ImpactMetric] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


# ----------------------------------------------------------------------------- schema helper
def inline_schema(model: type[BaseModel]) -> dict:
    """JSON schema with $defs inlined (tool input schemas and --json-schema prefer flat schemas)."""
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def resolve(node):
        if isinstance(node, dict):
            if "$ref" in node:
                return resolve(defs[node["$ref"].split("/")[-1]])
            # drop pydantic's "title" annotations, but keep a *property* that happens to be named title
            return {k: resolve(v) for k, v in node.items() if not (k == "title" and isinstance(v, str))}
        if isinstance(node, list):
            return [resolve(x) for x in node]
        return node

    return resolve(schema)
