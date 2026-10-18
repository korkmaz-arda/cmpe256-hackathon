"""Source manifest: the single, explicit list of documents each agent is grounded on.

Only course-provided material is listed here (resources/data/*.zip, the official link lists in
resources/documents/*.txt and the offline copies of those links in resources/web/). Agent prompts
render their "Grounding sources" section from this manifest, and tests check that every entry
exists on disk and that the web entries match the official link lists, so prompt, docs and code
cannot drift apart.

Path prefixes:
  res:  relative to CONSULTAI_RESOURCES (read-only course resources)
  raw:  relative to CONSULTAI_DATA_ROOT/raw (unzipped course data)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from consultai.config import RAW_DIR, RESOURCES_DIR


@dataclass(frozen=True)
class Source:
    source_id: str
    agent: str                 # technology | clinical | sec | csr
    collection: str            # retrieval index this source is chunked into
    title: str
    kind: str                  # pdf | html | csv
    path: str                  # "res:..." or "raw:..."
    citation_url: str | None   # URL shown to the user; None for course files without a public URL
    origin: str                # where the course provided it
    meta: dict = field(default_factory=dict)
    canonical_url: str | None = None  # URL the saved page itself declares, when it differs

    @property
    def local_path(self) -> Path:
        prefix, rel = self.path.split(":", 1)
        return (RESOURCES_DIR if prefix == "res" else RAW_DIR) / rel

    def cite(self, locator: str | None = None) -> str:
        """Human-readable citation, e.g. 'Cisco 10-K FY2026 (accession ...), p. 34'."""
        return f"{self.title}, {locator}" if locator else self.title


# --------------------------------------------------------------------------------------------
# Technology agent: Cisco router documentation (resources/documents/DataSource-Cisco.txt) and
# Google Cloud pages (resources/documents/Google GCP.txt). Offline copies: resources/web/{cisco,gcp}
# with sources.tsv mapping file -> URL. No IBM material was provided.
# --------------------------------------------------------------------------------------------
_CISCO = [
    # (slug, family title, product page URL, datasheet URL, canonical page URL of the saved copy)
    ("catalyst-8300", "Cisco Catalyst 8300 Series Edge Platforms",
     "https://www.cisco.com/c/en/us/products/routers/catalyst-8300-series-edge-platforms/index.html",
     "https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8300-series-edge-platforms/datasheet-c78-744088.pdf",
     "https://www.cisco.com/site/us/en/products/networking/sdwan-routers/catalyst-8300-series-platforms/index.html"),
    ("catalyst-8200", "Cisco Catalyst 8200 Series Edge Platforms",
     "https://www.cisco.com/c/en/us/products/routers/catalyst-8200-series-edge-platforms/index.html",
     "https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8200-series-edge-platforms/nb-06-cat8200-series-edge-plat-ds-cte-en.pdf",
     "https://www.cisco.com/site/us/en/products/networking/sdwan-routers/catalyst-8200-series-platforms/index.html"),
    ("catalyst-8000v", "Cisco Catalyst 8000V Edge Software",
     "https://www.cisco.com/c/en/us/products/routers/catalyst-8000v-edge-software/index.html",
     "https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8000v-edge-software/catalyst-8000v-edge-software-ds.pdf",
     "https://www.cisco.com/site/us/en/products/networking/sdwan-routers/catalyst-8000v-edge-software/index.html"),
    ("isr-4000", "Cisco 4000 Series Integrated Services Routers (ISR)",
     "https://www.cisco.com/c/en/us/products/routers/4000-series-integrated-services-routers-isr/index.html",
     "https://www.cisco.com/c/en/us/products/collateral/routers/4000-series-integrated-services-routers-isr/data_sheet-c78-732542.pdf",
     "https://www.cisco.com/site/us/en/products/networking/sdwan-routers/4000-series-integrated-services-routers/index.html"),
    ("asr-1000", "Cisco ASR 1000 Series Aggregation Services Routers",
     "https://www.cisco.com/c/en/us/products/routers/asr-1000-series-aggregation-services-routers/index.html",
     "https://www.cisco.com/c/en/us/products/collateral/routers/asr-1000-series-aggregation-services-routers/datasheet-c78-731632.pdf",
     "https://www.cisco.com/site/us/en/products/networking/sdwan-routers/asr-1000-series-aggregation-services-routers/index.html"),
]

TECH_SOURCES: list[Source] = []
for slug, family, page_url, ds_url, canonical in _CISCO:
    TECH_SOURCES.append(Source(
        f"cisco-{slug}-datasheet", "technology", "tech_docs", f"{family} - Data Sheet", "pdf",
        f"res:web/cisco/{slug}_datasheet.pdf", ds_url, "documents/DataSource-Cisco.txt",
        {"vendor": "Cisco", "family": slug}))
    TECH_SOURCES.append(Source(
        f"cisco-{slug}-page", "technology", "tech_docs", f"{family} - Product Page", "html",
        f"res:web/cisco/{slug}_page.html", page_url, "documents/DataSource-Cisco.txt",
        {"vendor": "Cisco", "family": slug}, canonical_url=canonical))

TECH_SOURCES += [
    Source("gcp-mcp-overview", "technology", "tech_docs", "Google Cloud MCP servers overview", "html",
           "res:web/gcp/mcp-overview.html", "https://docs.cloud.google.com/mcp/overview",
           "documents/Google GCP.txt", {"vendor": "Google", "family": "gcp-mcp"}),
    Source("gcp-what-is-mcp", "technology", "tech_docs", "Google Cloud - What is Model Context Protocol (MCP)?", "html",
           "res:web/gcp/what-is-mcp.html", "https://cloud.google.com/discover/what-is-model-context-protocol",
           "documents/Google GCP.txt", {"vendor": "Google", "family": "gcp-mcp"}),
    Source("gcp-rag", "technology", "tech_docs", "Google Cloud - What is Retrieval-Augmented Generation (RAG)?", "html",
           "res:web/gcp/rag-use-case.html", "https://cloud.google.com/use-cases/retrieval-augmented-generation",
           "documents/Google GCP.txt", {"vendor": "Google", "family": "gcp-rag"}),
]

# --------------------------------------------------------------------------------------------
# Clinical agent: Agilent web pages (resources/documents/Agilent.txt; browser saves named by page
# title in resources/web/agilent, matched to URLs via <link rel=canonical>; the press release has
# no canonical link and is matched by its title), IEEE papers and ClinicalTrials.gov exports
# (resources/data/Clinical.zip).
# --------------------------------------------------------------------------------------------
_AGILENT = [
    ("agilent-seahorse-xf", "Agilent - Real-Time Cell Metabolic Analysis, Seahorse XF",
     "Real-Time Cell Metabolic Analysis, Seahorse XF _ Agilent.html",
     "https://www.agilent.com/en/product/cell-analysis/real-time-cell-metabolic-analysis"),
    ("agilent-press-2023-scientists-choice", "Agilent press release (Mar 7, 2023) - Agilent Wins Two Scientists' Choice Awards for Drug Discovery & Development",
     "Agilent Wins Two Scientists' Choice Awards for Drug Discovery & Development.html",
     "https://www.agilent.com/about/newsroom/presrel/2023/07mar-ca23010.html"),
    ("agilent-digital-pathology", "Agilent - Digital Pathology",
     "Digital Pathology _ Agilent.html",
     "https://www.agilent.com/en/product/digital-pathology"),
    ("agilent-digital-pathology-scanners", "Agilent - Digital Pathology Scanners",
     "Digital Pathology Scanners _ Agilent.html",
     "https://www.agilent.com/en/product/digital-pathology/digital-pathology-scanners"),
    ("agilent-nanozoomer", "Agilent - NanoZoomer Slide Scanner System (IVD)",
     "Digital Pathology Scanner, NanoZoomer Slide Scanner System _ Agilent.html",
     "https://www.agilent.com/en/product/digital-pathology/digital-pathology-scanners/nanozoomer-slide-scanner-system-4370282"),
    ("agilent-artisan-link-pro", "Agilent - Artisan Link Pro for Special Stains",
     "Artisan Link Pro for Special Stains _ Agilent.html",
     "https://www.agilent.com/en/product/special-stains"),
]
CLINICAL_SOURCES: list[Source] = [
    Source(sid, "clinical", "agilent", title, "html", f"res:web/agilent/{fname}", url,
           "documents/Agilent.txt", {"vendor": "Agilent"})
    for sid, title, fname, url in _AGILENT
]

_PAPERS = {
    "Covid": [
        "Analysis_and_Prediction_of_COVID-19_using_Machine_Learning",
        "Big_Data_Analytics_on_Irritating_Anxiety_of_Long_COVID",
        "COVID-19_Update_Forecast_and_Assistant_-_An_Interactive_Web_Portal_to_Provide_Real-Time_Information_and_Forecast_COVID-19_Cases_in_Bangladesh",
        "COVID_Detection_using_Deep_Learning",
        "Extraction_of_Features_from_Lung_Image_for_the_Detection_of_Covid-19",
    ],
    "Diabetes": [
        "Artificial_Intelligence_and_Machine_Learning_for_Improving_Glycemic_Control_in_Diabetes_Best_Practices_Pitfalls_and_Opportunities",
        "Deep_Learning-Based_Genetic_Detection_and_Pathogenesis_of_Diabetes",
        "Exploring_Biomarker_Relationships_in_Both_Type_1_and_Type_2_Diabetes_Mellitus_Through_a_Bayesian_Network_Analysis_Approach",
        "Improving_Self-Management_of_Type_2_Diabetes_Evaluating_the_Effectiveness_of_a_Mobile_App-Based_Patient_Education_Approach",
        "Knowledge-Infused_LLM-Powered_Conversational_Health_Agent_A_Case_Study_for_Diabetes_Patients",
    ],
    "Heart_attack": [
        "Fog-Driven_Heart_Attack_Prediction_from_Wearable_Edge_Devices",
        "IOT_Based_Heart_Rate_Monitoring_System_Design_for_Heart_Attack_Detection",
        "Machine_Learning_Approaches_for_Predicting_Heart_Attacks",
        "Machine_Learning_Model_for_Heart_Disease_Detection_A_Comparative_Analysis_of_SVM_vs_KNN",
        "Prediction_of_Heart_Disease_using_Machine_Learning_Technique",
    ],
    "KneeInjuries": [
        "A_Comprehensive_Review_of_Knee_Abnormalities_Detection_Current_Procedures_Outcomes_and_Prospects",
        "Design_and_Analysis_of_a_Knee_Exoskeleton_with_Self-alignment_Capability",
        "Design_and_control_of_a_novel_powered_wearable_knee_exoskeleton_for_lower_limb_rehabilitation",
        "Development_of_a_Highlighting_System_for_Surgical_Instruments_in_Total_Knee_Arthroplasty",
        "Knee_Fracture_Surgery_Monitoring_for_Advanced_Post-Operative_System_Using_IOT",
    ],
}
TOPIC_LABEL = {"Covid": "covid", "Diabetes": "diabetes", "Heart_attack": "heart_attack", "KneeInjuries": "knee_injuries"}

for folder, stems in _PAPERS.items():
    for stem in stems:
        CLINICAL_SOURCES.append(Source(
            f"paper-{TOPIC_LABEL[folder]}-{stem[:40].lower().strip('_-')}", "clinical", "clinical_lit",
            f"IEEE paper: {stem.replace('_', ' ')}", "pdf", f"raw:Clinical/{folder}/{stem}.pdf", None,
            "data/Clinical.zip", {"topic": TOPIC_LABEL[folder]}))

TRIAL_SETS = {  # condition_set -> CSV in Clinical.zip (ClinicalTrials.gov exports)
    "covid": "ctg-studies_covid.csv",
    "diabetes": "ctg-studies_diabetes.csv",
    "heart_attack": "ctg-studies_Hearattack.csv",
    "knee_injuries": "ctg-studies_KneeInjuries.csv",
}
for cset, fname in TRIAL_SETS.items():
    CLINICAL_SOURCES.append(Source(
        f"ctg-{cset}", "clinical", "trials", f"ClinicalTrials.gov export: {cset.replace('_', ' ')} studies", "csv",
        f"raw:Clinical/{fname}", None, "data/Clinical.zip", {"condition_set": cset}))

# --------------------------------------------------------------------------------------------
# SEC agent: Form 10-K annual reports (resources/data/UnitedStatesSecuritiesandExchangeCommission(SEC).zip).
# Files are named by UUID; company / fiscal year / accession number were read from each cover page
# and the PDF metadata, and ingestion re-checks the cover page against this table.
# --------------------------------------------------------------------------------------------
_SEC_DIR = "UnitedStatesSecuritiesandExchangeCommission(SEC)"
_FILINGS = [
    # (company, folder, uuid, fiscal year, fiscal year end, accession number, cover-page name)
    ("Agilent", "Agilent", "b5098e8e-5716-4b35-8d8e-84dbdab516b1", 2025, "2025-10-31", "0001090872-25-000087", "Agilent Technologies, Inc."),
    ("Alphabet", "Alphabet", "0ca59726-c36c-45fe-a114-e147f8cd7237", 2024, "2024-12-31", "0001652044-25-000014", "Alphabet Inc."),
    ("Alphabet", "Alphabet", "8873e505-7403-4c46-b377-81d814482cbb", 2025, "2025-12-31", "0001652044-26-000018", "Alphabet Inc."),
    ("Cisco", "Cisco", "6c821d1a-cf4e-4310-9801-df9399aa701b", 2025, "2025-07-26", "0000858877-25-000111", "CISCO SYSTEMS, INC."),
    ("Cisco", "Cisco", "028fbac9-c5ba-409b-83ce-dfee9c17fdbc", 2026, "2026-07-25", "0000858877-26-000132", "CISCO SYSTEMS, INC."),
]
SEC_SOURCES: list[Source] = [
    Source(f"10k-{company.lower()}-fy{fy}", "sec", "sec_filings",
           f"{company} Form 10-K, fiscal year ended {fye} (accession {acc})", "pdf",
           f"raw:{_SEC_DIR}/{folder}/{uuid}.pdf", None, "data/UnitedStatesSecuritiesandExchangeCommission(SEC).zip",
           {"company": company, "fiscal_year": fy, "fiscal_year_end": fye, "accession": acc, "cover_name": cover})
    for company, folder, uuid, fy, fye, acc, cover in _FILINGS
]

# --------------------------------------------------------------------------------------------
# Corporate Responsibility agent: FAO et al., The State of Food Security and Nutrition in the World
# (SOFI) 2023 and 2024 (resources/data/FoodSecurity.zip).
# --------------------------------------------------------------------------------------------
CSR_SOURCES: list[Source] = [
    Source("sofi-2023", "csr", "sofi",
           "FAO, IFAD, UNICEF, WFP and WHO - The State of Food Security and Nutrition in the World 2023 (SOFI 2023)",
           "pdf", "raw:FoodSecurity/SOFI-2023.pdf", None, "data/FoodSecurity.zip",
           {"edition": 2023, "theme": "Urbanization, agrifood systems transformation and healthy diets across the rural-urban continuum"}),
    Source("sofi-2024", "csr", "sofi",
           "FAO, IFAD, UNICEF, WFP and WHO - The State of Food Security and Nutrition in the World 2024 (SOFI 2024)",
           "pdf", "raw:FoodSecurity/SOFI-2024.pdf", None, "data/FoodSecurity.zip",
           {"edition": 2024, "theme": "Financing to end hunger, food insecurity and malnutrition in all its forms"}),
]

# Market-basket data (optional task; not used for agent grounding).
RETAIL_TRANSACTIONS = "raw:Retail/CMPE256_Hackathon_market_basket_analysis_Release.csv"

ALL_SOURCES: list[Source] = TECH_SOURCES + CLINICAL_SOURCES + SEC_SOURCES + CSR_SOURCES
SOURCES_BY_ID: dict[str, Source] = {s.source_id: s for s in ALL_SOURCES}

# Things a customer may ask about that we were NOT given data for. Agents state these gaps.
KNOWN_GAPS: dict[str, list[str]] = {
    "technology": [
        "IBM: named in the brief, but no IBM documentation was provided - nothing about IBM can be grounded.",
        "Cisco: only data sheets and product pages for five router families; no troubleshooting guides, "
        "field notices, configuration guides or pricing.",
        "Google: only three Google Cloud pages (MCP overview, what is MCP, what is RAG); no product pricing or SLAs.",
    ],
    "clinical": [
        "Agilent: six web pages (Seahorse XF, digital pathology, scanners, NanoZoomer, Artisan Link Pro, one press release); "
        "no instrument manuals, service guides, part catalogs or prices.",
        "Literature: 20 IEEE papers (5 each on COVID-19, diabetes, heart attack, knee injuries); not a systematic review.",
        "Trials: ClinicalTrials.gov exports for four condition sets only; registry metadata, not outcome data.",
    ],
    "sec": [
        "Five Form 10-K filings only: Agilent FY2025, Alphabet FY2024 and FY2025, Cisco FY2025 and FY2026. "
        "No 10-Qs, 8-Ks, proxy statements, earnings calls, stock prices or analyst estimates.",
    ],
    "csr": [
        "Two reports only: SOFI 2023 and SOFI 2024. No company ESG/CSR reports or other sustainability datasets.",
    ],
}


def sources_for(agent: str) -> list[Source]:
    return [s for s in ALL_SOURCES if s.agent == agent]


def collection_sources(collection: str) -> list[Source]:
    return [s for s in ALL_SOURCES if s.collection == collection]
