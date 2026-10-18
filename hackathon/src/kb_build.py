"""Build the domain knowledge bases: extract PDFs, chunk all sources, save kb.json.

Domains:
  technology -> DataSource-Cisco.txt, Google_GCP.txt (+ product catalog from retail CSV)
  clinical   -> Agilent.txt
  sec        -> Cisco / Alphabet / Agilent 2025 SEC filings (PDF)
  csr        -> SOFI 2023 / 2024 food-security reports (PDF)
"""
import json
import re
import zipfile
from pathlib import Path

from pypdf import PdfReader

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
KB_DIR = Path(__file__).resolve().parent.parent / "data" / "kb"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


def clean(text: str) -> str:
    text = (text.replace("ﬁ", "fi").replace("ﬂ", "fl")
            .replace("ﬀ", "ff").replace("ﬃ", "ffi"))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    text = clean(text)
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        # try to break on a sentence/paragraph boundary
        if end < len(text):
            cut = max(text.rfind(". ", start, end), text.rfind("\n", start, end))
            if cut > start + size // 2:
                end = cut + 1
        piece = text[start:end].strip()
        if len(piece) > 80:
            chunks.append(piece)
        start = max(end - overlap, start + 1) if end < len(text) else len(text)
    return chunks


def read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for p in reader.pages:
        try:
            pages.append(p.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n".join(pages)


def extract_zip(zip_path: Path, dest: Path):
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest)


def build_trial_summaries(clinical_dir: Path) -> str:
    """Aggregate the 4 ClinicalTrials.gov CSVs into citable summary texts.

    Chunking 121k raw rows would flood the index; aggregates plus samples
    keep the registry grounded and searchable.
    """
    import pandas as pd
    blocks = []
    labels = {"covid": "COVID-19", "diabetes": "diabetes",
              "Hearattack": "heart attack / heart disease",
              "KneeInjuries": "knee injuries"}
    for csv in sorted(clinical_dir.glob("ctg-studies_*.csv")):
        key = csv.stem.replace("ctg-studies_", "")
        area = labels.get(key, key)
        try:
            df = pd.read_csv(csv, low_memory=False)
        except Exception:
            continue
        n = len(df)
        status = df["Study Status"].fillna("UNKNOWN").str.upper().value_counts()
        status_s = ", ".join(f"{s} {c}" for s, c in status.head(6).items())
        blob = (df["Study Title"].fillna("") + " " +
                df["Brief Summary"].fillna("") + " " +
                df["Interventions"].fillna(""))
        blo = blob.str.lower()
        lines = [f"ClinicalTrials.gov {area} studies registry summary. "
                 f"Total studies indexed: {n:,}. By status: {status_s}."]
        for term, label in [("seahorse", "Seahorse XF real-time cell metabolic "
                                        "analysis"),
                            ("mitochondrial", "mitochondrial function")]:
            hit = df[blo.str.contains(term, na=False)]
            if len(hit):
                samples = "; ".join(
                    f"{r['NCT Number']}: {str(r['Study Title'])[:90]}"
                    for _, r in hit.head(8).iterrows())
                lines.append(
                    f"Studies mentioning {label}: {len(hit)}. Examples: "
                    f"{samples}.")
            else:
                lines.append(f"Studies mentioning {label}: none indexed.")
        conds = df["Conditions"].fillna("").str.split("|").explode(
            ).str.strip()
        conds = conds[conds != ""].value_counts().head(8)
        if len(conds):
            lines.append("Most common conditions: " +
                         ", ".join(f"{c} ({v})" for c, v in conds.items()) +
                         ".")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build():
    tmp = KB_DIR / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    extract_zip(RAW / "UnitedStatesSecuritiesandExchangeCommission_SEC.zip", tmp / "sec")
    extract_zip(RAW / "FoodSecurity_0_oixi.zip", tmp / "food")

    chunks = []

    def add(domain, source_label, text):
        for i, c in enumerate(chunk_text(text)):
            chunks.append({
                "id": f"{domain}-{len(chunks):05d}",
                "domain": domain,
                "source": source_label,
                "text": c,
            })

    # ---- technology ----
    add("technology", "Cisco product datasheets (DataSource-Cisco.txt)",
        read_txt(RAW / "DataSource-Cisco.txt"))
    add("technology", "Google Cloud docs (Google_GCP.txt)",
        read_txt(RAW / "Google_GCP.txt"))

    # ---- fetched authoritative pages (linked from the supplied txt files) ----
    fetched = RAW / "fetched"
    fetched_map = {
        "cisco_catalyst_8300.txt": ("technology", "Cisco Catalyst 8300 Series Edge Platforms (cisco.com)"),
        "cisco_isr4000.txt": ("technology", "Cisco 4000 Series ISR, incl. end-of-sale notice (cisco.com)"),
        "cisco_asr1000.txt": ("technology", "Cisco ASR 1000 Series (cisco.com)"),
        "gcp_rag.txt": ("technology", "Google Cloud: What is RAG? (cloud.google.com)"),
        "agilent_seahorse.txt": ("clinical", "Agilent Seahorse Real-Time Cell Metabolic Analysis (agilent.com)"),
        "agilent_nanozoomer.txt": ("clinical", "Agilent NanoZoomer Slide Scanner System (agilent.com)"),
        "agilent_artisan.txt": ("clinical", "Agilent Artisan Link Pro Special Stains (agilent.com)"),
    }
    if fetched.exists():
        for fname, (domain, label) in fetched_map.items():
            p = fetched / fname
            if p.exists():
                add(domain, label, read_txt(p))

    # ---- clinical ----
    add("clinical", "Agilent product portfolio (Agilent.txt)",
        read_txt(RAW / "Agilent.txt"))

    # ---- clinical: IEEE papers + ClinicalTrials.gov registry ----
    clinical_dir = RAW / "Clinical"
    if clinical_dir.exists():
        for pdf in sorted(clinical_dir.rglob("*.pdf")):
            area = pdf.parent.name.replace("_", " ")
            add("clinical",
                f"IEEE paper on {area} ({pdf.stem[:44]}..)",
                read_pdf(pdf))
        add("clinical",
            "ClinicalTrials.gov registry summaries (32,611 studies)",
            build_trial_summaries(clinical_dir))

    # ---- sec filings ----
    sec_root = tmp / "sec"
    for pdf in sorted(sec_root.rglob("*.pdf")):
        company = pdf.parent.name  # Cisco / Alphabet / Agilent
        add("sec", f"{company} SEC filing ({pdf.stem[:8]}…)",
            read_pdf(pdf))

    # ---- corporate responsibility / food security ----
    food_root = tmp / "food"
    for pdf in sorted(food_root.rglob("SOFI-*.pdf")):
        year = "2024" if "2024" in pdf.name else "2023"
        add("csr", f"FAO SOFI {year} – State of Food Security and Nutrition",
            read_pdf(pdf))

    # ---- product catalog from the retail market-basket CSV (tech agent) ----
    import csv
    catalog_items = {}
    with open(RAW / "CMPE256_Hackathon_market_basket_analysis_Release.csv",
              newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for k in ("item_1", "item_2", "item_3", "item_4", "item_5"):
                name = (row.get(k) or "").strip()
                if name:
                    catalog_items[name] = catalog_items.get(name, 0) + 1
    catalog = []
    for name, freq in sorted(catalog_items.items(), key=lambda x: -x[1]):
        m = re.search(r"\(SKU:\s*([^)]+)\)", name)
        sku = m.group(1) if m else ""
        lname = name.lower()
        if "camera" in lname:
            cat = "IP/Network camera"
        elif "nvr" in lname:
            cat = "Network video recorder"
        elif "detector" in lname:
            cat = "Detector (CO/glassbreak)"
        elif "panel" in lname:
            cat = "Control panel"
        elif "base" in lname:
            cat = "Detector base"
        else:
            cat = "Security component"
        catalog.append({"name": name, "sku": sku, "category": cat,
                        "purchase_frequency": freq})
    catalog_text = ".\n".join(
        f"{c['name']} | category: {c['category']} | bought in {c['purchase_frequency']} transactions"
        for c in catalog)
    add("technology", "Procurement catalog (1,000 historical transactions)",
        catalog_text)

    KB_DIR.mkdir(parents=True, exist_ok=True)
    with open(KB_DIR / "kb.json", "w", encoding="utf-8") as f:
        json.dump({"chunks": chunks}, f, ensure_ascii=False)
    with open(KB_DIR / "catalog.json", "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=1)

    by_domain = {}
    for c in chunks:
        by_domain[c["domain"]] = by_domain.get(c["domain"], 0) + 1
    print(f"chunks: {len(chunks)}  by domain: {by_domain}")
    print(f"catalog items: {len(catalog)}")
    # cleanup extracted pdfs (keep zips in raw/)
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    build()
