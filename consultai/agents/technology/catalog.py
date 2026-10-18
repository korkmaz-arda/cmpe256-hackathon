"""Cisco platform & component catalog + the platform recommender used by the Technology agent.

The catalog is extracted from the five Cisco data sheets by `scripts/extract_catalogs.py`
(Claude reads each data sheet; code then VERIFIES every part number and every attribute value
string against the text of the page it was cited from, and drops anything that does not match).
Lifecycle status (end-of-sale / end-of-support) is parsed with a regex from the saved product pages.

`recommend_platforms` is a transparent content-based recommender:
  1. hard constraints   - virtual vs physical, 10G WAN, minimum ports/slots/throughput (exclusions are reported)
  2. requirement fit    - share of requested numeric requirements met by *verified* attributes
  3. similarity match   - cosine similarity of the customer's use case to each platform summary (bge embeddings)
  4. context            - deployment-role match, right-sizing (penalise capacity far above the stated need),
                          headroom over the current model, lifecycle penalty for end-of-sale families
     (the right-sizing term was added after the recommendation evaluation showed oversized picks for a
      small branch; see eval/results/recommendation.json)
Every score component is returned, so the agent (and the customer) can see why an option ranks where it does.
"""
from __future__ import annotations

import json
import math
import re
from functools import lru_cache

from pydantic import BaseModel, Field

from consultai.config import INDEX_DIR
from consultai.ingest.extract import html_documents
from consultai.ingest.sources import SOURCES_BY_ID, TECH_SOURCES

CATALOG_PATH = INDEX_DIR / "catalogs" / "cisco_catalog.json"
FAMILIES = ["catalyst-8300", "catalyst-8200", "catalyst-8000v", "isr-4000", "asr-1000"]


# ----------------------------------------------------------------------------- extraction schema
class AttributeEvidence(BaseModel):
    attribute: str
    value_text: str = Field(description="The value exactly as printed on the page, e.g. '19 Gbps' or '2 x 10Gbps'")
    page: int


class PlatformAttributes(BaseModel):
    wan_1g_ports: int | None = None
    wan_10g_ports: int | None = None
    nim_slots: int | None = None
    sm_slots: int | None = None
    ipsec_throughput_gbps: float | None = Field(None, description="Max IPsec throughput in Gbps as stated (convert Mbps)")
    forwarding_throughput_gbps: float | None = Field(None, description="Max forwarding/aggregate throughput in Gbps")
    dram_default_gb: float | None = None
    dram_max_gb: float | None = None
    redundant_power: bool | None = None
    poe: bool | None = None
    rack_units: float | None = None
    virtual: bool = False


class Platform(BaseModel):
    model: str = Field(description="Exact model / product id as printed, e.g. C8300-1N1S-6T, ISR4451, ASR1001-HX, C8000V")
    family: str = Field(description="catalyst-8300 | catalyst-8200 | catalyst-8000v | isr-4000 | asr-1000")
    summary: str = Field(description="One or two sentences: what the model is for, from the data sheet")
    page: int
    deployment: list[str] = Field(default_factory=list, description="branch | aggregation | headend | cloud | colocation")
    attributes: PlatformAttributes
    attribute_evidence: list[AttributeEvidence] = Field(default_factory=list)


class Component(BaseModel):
    pid: str = Field(description="Exact orderable product id as printed, e.g. PWR-CC1-500WAC, NIM-2GE-CU-SFP, MEM-C8300-16GB")
    category: str = Field(description="power_supply | network_module | service_module | memory | storage | license | "
                                      "route_processor | embedded_services_processor | accessory | other")
    description: str
    applies_to: list[str] = Field(default_factory=list, description="Models or the family this part is for")
    page: int


class DatasheetExtraction(BaseModel):
    platforms: list[Platform] = Field(default_factory=list)
    components: list[Component] = Field(default_factory=list)


# ----------------------------------------------------------------------------- verification
def norm(text: str) -> str:
    """Collapse whitespace and re-join part numbers broken across lines ('PWR-CC1-\\n250WAC')."""
    text = re.sub(r"-\s+", "-", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def verify_extraction(source_id: str, ext: DatasheetExtraction, pages: dict[int, str]) -> tuple[DatasheetExtraction, dict]:
    """Keep only what the cited page actually says. Returns the verified extraction and a report."""
    npages = {p: norm(t) for p, t in pages.items()}
    report = {"source_id": source_id, "platforms_in": len(ext.platforms), "components_in": len(ext.components),
              "dropped_platforms": [], "dropped_components": [], "dropped_attributes": []}
    kept_platforms = []
    for p in ext.platforms:
        if norm(p.model) not in npages.get(p.page, ""):
            hit = next((pg for pg, t in npages.items() if norm(p.model) in t), None)
            if hit is None:
                report["dropped_platforms"].append(p.model)
                continue
            p.page = hit
        verified, attrs = [], p.attributes.model_dump()
        for ev in p.attribute_evidence:
            if ev.attribute in attrs and norm(ev.value_text) in npages.get(ev.page, ""):
                verified.append(ev)
            else:
                report["dropped_attributes"].append(f"{p.model}.{ev.attribute}={ev.value_text!r} (p.{ev.page})")
        verified_names = {ev.attribute for ev in verified}
        # numeric/boolean attributes without a verified value string are cleared (unknown, not guessed)
        for name in list(attrs):
            if name == "virtual":
                continue
            if attrs[name] is not None and name not in verified_names:
                report["dropped_attributes"].append(f"{p.model}.{name} (no verifiable value text)")
                attrs[name] = None
        p.attributes = PlatformAttributes(**attrs)
        p.attribute_evidence = verified
        kept_platforms.append(p)
    kept_components = []
    for c in ext.components:
        page_text = npages.get(c.page, "")
        if norm(c.pid) in page_text:
            kept_components.append(c)
            continue
        hit = next((pg for pg, t in npages.items() if norm(c.pid) in t), None)
        if hit is None:
            report["dropped_components"].append(c.pid)
        else:
            c.page = hit
            kept_components.append(c)
    report.update(platforms_out=len(kept_platforms), components_out=len(kept_components))
    return DatasheetExtraction(platforms=kept_platforms, components=kept_components), report


# ----------------------------------------------------------------------------- lifecycle (regex, no LLM)
@lru_cache
def lifecycle() -> dict[str, dict]:
    pages = [s for s in TECH_SOURCES if s.source_id.endswith("-page")]
    texts = html_documents([s.local_path for s in pages])
    out = {}
    for s in pages:
        text = texts[s.local_path]
        eos = re.search(r"End-of-sale date:\s*([A-Z][a-z]+ \d{1,2}, \d{4})", text)
        eol = re.search(r"End-of-support date:\s*([A-Z][a-z]+ \d{1,2}, \d{4})", text)
        out[s.meta["family"]] = {"end_of_sale": eos.group(1) if eos else None,
                                 "end_of_support": eol.group(1) if eol else None,
                                 "source_id": s.source_id}
    return out


# ----------------------------------------------------------------------------- catalog access
@lru_cache
def load_catalog() -> dict:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError("Cisco catalog not built. Run: python scripts/extract_catalogs.py --cisco")
    return json.loads(CATALOG_PATH.read_text())


def platforms() -> list[Platform]:
    return [Platform.model_validate(p) for p in load_catalog()["platforms"]]


def components() -> list[Component]:
    return [Component.model_validate(c) for c in load_catalog()["components"]]


def family_of_model(model: str) -> str | None:
    m = model.upper().replace(" ", "")
    for p in platforms():
        if p.model.upper() == m:
            return p.family
    rules = [(r"^C83", "catalyst-8300"), (r"^C82", "catalyst-8200"), (r"^C8000V|^C8K-?V", "catalyst-8000v"),
             (r"^ISR4|^ISR-4", "isr-4000"), (r"^ASR1|^ASR-1", "asr-1000")]
    return next((fam for pat, fam in rules if re.match(pat, m)), None)


# ----------------------------------------------------------------------------- recommender
class PlatformRequirements(BaseModel):
    use_case: str = Field(description="Customer's situation in their words (sites, traffic, services, cloud, ...)")
    deployment: str | None = Field(None, description="branch | aggregation | headend | cloud | colocation")
    virtual_required: bool | None = Field(None, description="True = must be virtual/cloud; False = must be hardware")
    current_model: str | None = Field(None, description="Model being replaced, e.g. ISR4331")
    min_ipsec_gbps: float | None = None
    min_forwarding_gbps: float | None = None
    min_wan_ports: int | None = None
    need_10g_wan: bool | None = None
    min_nim_slots: int | None = None
    need_redundant_power: bool | None = None
    need_poe: bool | None = None
    k: int = 5


W_SIMILARITY, W_FIT, W_CONTEXT, LIFECYCLE_PENALTY = 0.40, 0.35, 0.25, 0.35


def _sizing(req: "PlatformRequirements", a: PlatformAttributes) -> float:
    """1.0 when verified capacity is within 4x of the stated need, decaying for oversized platforms;
    0.5 (neutral) when there is no stated need or no verified value to compare."""
    pairs = [(req.min_ipsec_gbps, a.ipsec_throughput_gbps), (req.min_forwarding_gbps, a.forwarding_throughput_gbps)]
    ratios = [have / need for need, have in pairs if need and have]
    if not ratios:
        return 0.5
    ratio = max(ratios)
    return 1.0 if ratio <= 4 else max(0.0, 1.0 - math.log2(ratio / 4) / 4)


def _numeric_checks(req: PlatformRequirements, a: PlatformAttributes) -> list[tuple[str, bool | None]]:
    """(requirement, met?) where None = attribute not verified in the data sheet."""
    checks = []

    def ge(name: str, need, have):
        if need is not None:
            checks.append((f"{name} >= {need}", None if have is None else have >= need))

    ge("IPsec Gbps", req.min_ipsec_gbps, a.ipsec_throughput_gbps)
    ge("forwarding Gbps", req.min_forwarding_gbps, a.forwarding_throughput_gbps)
    total_wan = None if a.wan_1g_ports is None and a.wan_10g_ports is None else (a.wan_1g_ports or 0) + (a.wan_10g_ports or 0)
    ge("WAN ports", req.min_wan_ports, total_wan)
    ge("NIM slots", req.min_nim_slots, a.nim_slots)
    if req.need_10g_wan:
        checks.append(("10G WAN", None if a.wan_10g_ports is None else a.wan_10g_ports >= 1))
    if req.need_redundant_power:
        checks.append(("redundant power", a.redundant_power))
    if req.need_poe:
        checks.append(("PoE", a.poe))
    return checks


def recommend_platforms(req: PlatformRequirements) -> dict:
    from consultai.retrieval.models import embed_passages, embed_query

    plats = platforms()
    life = lifecycle()
    baseline = None
    if req.current_model:
        baseline = next((p for p in plats if p.model.upper() == req.current_model.upper().replace(" ", "")), None)
        # replacing a model: by default require at least its verified capacity
        if baseline:
            ba = baseline.attributes
            req.min_ipsec_gbps = req.min_ipsec_gbps or ba.ipsec_throughput_gbps
            req.min_wan_ports = req.min_wan_ports or (None if ba.wan_1g_ports is None and ba.wan_10g_ports is None
                                                      else (ba.wan_1g_ports or 0) + (ba.wan_10g_ports or 0))
    qv = embed_query(req.use_case)
    pv = embed_passages([f"{p.model}: {p.summary} Deployment: {', '.join(p.deployment)}" for p in plats])
    ranked, excluded = [], []
    for p, vec in zip(plats, pv):
        a = p.attributes
        if req.virtual_required is True and not a.virtual:
            excluded.append({"model": p.model, "reason": "hardware platform; a virtual router is required"})
            continue
        if req.virtual_required is False and a.virtual:
            excluded.append({"model": p.model, "reason": "virtual platform; hardware is required"})
            continue
        if baseline and p.model == baseline.model:
            continue
        checks = _numeric_checks(req, a)
        failed = [c for c, ok in checks if ok is False]
        if failed:
            excluded.append({"model": p.model, "reason": "does not meet: " + "; ".join(failed)})
            continue
        unverified = [c for c, ok in checks if ok is None]
        fit = 1.0 if not checks else sum(1 for _, ok in checks if ok) / len(checks)
        similarity = float(max(0.0, min(1.0, (float(qv @ vec) - 0.3) / 0.5)))  # rescale bge cosine ~[0.3, 0.8] -> [0, 1]
        context = 0.0
        if req.deployment and req.deployment in p.deployment:
            context += 0.5
        sizing = _sizing(req, a)
        context += 0.5 * sizing
        if baseline and a.ipsec_throughput_gbps and baseline.attributes.ipsec_throughput_gbps:
            context += 0.4 * min(1.0, math.log2(a.ipsec_throughput_gbps / baseline.attributes.ipsec_throughput_gbps + 1) / 3)
        lc = life.get(p.family, {})
        penalty = LIFECYCLE_PENALTY if lc.get("end_of_sale") else 0.0
        score = W_SIMILARITY * similarity + W_FIT * fit + W_CONTEXT * min(context, 1.0) - penalty
        ranked.append({
            "model": p.model, "family": p.family, "score": round(score, 3),
            "components": {"similarity": round(similarity, 3), "requirement_fit": round(fit, 3), "right_sizing": round(sizing, 3),
                           "context": round(min(context, 1.0), 3), "lifecycle_penalty": penalty},
            "requirements_unverified": unverified, "lifecycle": lc, "summary": p.summary,
            "attributes": {k: v for k, v in a.model_dump().items() if v not in (None, False)},
            "page": p.page,
        })
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return {"weights": {"similarity": W_SIMILARITY, "requirement_fit": W_FIT, "context": W_CONTEXT,
                        "lifecycle_penalty_if_end_of_sale": LIFECYCLE_PENALTY},
            "baseline": baseline.model if baseline else None,
            "baseline_family_lifecycle": life.get(family_of_model(req.current_model) or "", None) if req.current_model else None,
            "ranked": ranked[: req.k], "excluded": excluded}


def source_for_family(family: str, kind: str = "datasheet"):
    return SOURCES_BY_ID[f"cisco-{family}-{kind}"]
