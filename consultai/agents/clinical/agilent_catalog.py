"""Agilent product catalog (from the six Agilent web pages) + product recommender for the Clinical agent.

Built by `scripts/extract_catalogs.py --agilent`: Claude lists the products each page describes; code keeps
a product only if its name (or part number) appears on that page, and keeps a spec line only if the
text appears verbatim on the page.

`recommend_agilent_products` ranks products for a lab requirement:
  * regulatory filter  - if the use is clinical diagnosis, research-use-only (RUO) products are excluded
  * similarity match   - cosine similarity between the requirement and the product description (bge)
  * application match  - overlap between requested applications and the product's applications
"""
from __future__ import annotations

import json
from functools import lru_cache

from pydantic import BaseModel, Field

from consultai.config import INDEX_DIR

CATALOG_PATH = INDEX_DIR / "catalogs" / "agilent_catalog.json"


class SpecLine(BaseModel):
    text: str = Field(description="Specification or capability sentence copied verbatim from the page")


class AgilentProduct(BaseModel):
    name: str = Field(description="Product name as printed, e.g. 'NanoZoomer S360MD Slide Scanner System'")
    source_id: str
    category: str = Field(description="digital_pathology_scanner | image_management | pathology_ai_apps | "
                                      "special_stains | cell_metabolic_analysis | consumables | other")
    regulatory_status: str = Field(description="IVD | RUO | not stated - exactly as the page labels it")
    part_numbers: list[str] = Field(default_factory=list)
    applications: list[str] = Field(default_factory=list, description="e.g. primary diagnosis, histopathology, "
                                                                       "special staining, cell metabolism, drug discovery")
    summary: str
    specs: list[SpecLine] = Field(default_factory=list)


class AgilentExtraction(BaseModel):
    products: list[AgilentProduct] = Field(default_factory=list)


@lru_cache
def load_catalog() -> list[AgilentProduct]:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError("Agilent catalog not built. Run: python scripts/extract_catalogs.py --agilent")
    return [AgilentProduct.model_validate(p) for p in json.loads(CATALOG_PATH.read_text())["products"]]


class LabRequirements(BaseModel):
    need: str = Field(description="The lab's requirement in plain words (workflow, sample type, volume, goal)")
    clinical_diagnostic_use: bool | None = Field(None, description="True if results are used for patient diagnosis (IVD needed)")
    applications: list[str] = Field(default_factory=list)
    k: int = 4


def recommend_agilent_products(req: LabRequirements) -> dict:
    from consultai.retrieval.models import embed_passages, embed_query

    products = load_catalog()
    qv = embed_query(req.need)
    pv = embed_passages([f"{p.name}. {p.summary} Applications: {', '.join(p.applications)}" for p in products])
    wanted = {a.lower() for a in req.applications}
    ranked, excluded = [], []
    for p, vec in zip(products, pv):
        if req.clinical_diagnostic_use and p.regulatory_status.upper().startswith("RUO"):
            excluded.append({"product": p.name, "reason": "research use only (RUO); not for clinical diagnosis"})
            continue
        similarity = max(0.0, min(1.0, (float(qv @ vec) - 0.3) / 0.5))
        app_overlap = (len(wanted & {a.lower() for a in p.applications}) / len(wanted)) if wanted else 0.0
        regulatory_bonus = 0.15 if (req.clinical_diagnostic_use and p.regulatory_status.upper().startswith("IVD")) else 0.0
        score = 0.7 * similarity + 0.3 * app_overlap + regulatory_bonus
        ranked.append({"product": p.name, "score": round(score, 3), "source_id": p.source_id,
                       "components": {"similarity": round(similarity, 3), "application_overlap": round(app_overlap, 3),
                                      "regulatory_bonus": regulatory_bonus},
                       "regulatory_status": p.regulatory_status, "part_numbers": p.part_numbers,
                       "applications": p.applications, "summary": p.summary, "specs": [s.text for s in p.specs][:6]})
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return {"ranked": ranked[: req.k], "excluded": excluded,
            "weights": {"similarity": 0.7, "application_overlap": 0.3, "ivd_bonus_when_diagnostic_use": 0.15}}
