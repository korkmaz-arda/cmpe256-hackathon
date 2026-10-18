"""Structure-aware chunking.

Every chunk stays inside one PDF page (so a citation can name the exact page) or one web-page
section. Each chunk records the section it belongs to:
  * SEC 10-K     -> the Form 10-K Item (e.g. "Item 1A. Risk Factors")
  * SOFI reports -> the chapter from the running page header (e.g. "Chapter 2 Food security and ...")
  * IEEE papers  -> the roman-numeral section heading (e.g. "III. Methodology")
  * web pages    -> the nearest h1-h4 heading
The text that is indexed is prefixed with the document title and section, so BM25 and the
embedding model see where a passage comes from.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from consultai.ingest.sources import Source


@dataclass
class Chunk:
    chunk_id: str
    source_id: str
    collection: str
    text: str                   # passage as shown to agents
    page: int | None = None     # 1-based PDF page
    section: str | None = None
    meta: dict = field(default_factory=dict)

    @property
    def index_text(self) -> str:
        head = " | ".join(x for x in (self.meta.get("doc_title"), self.section) if x)
        return f"{head}\n{self.text}" if head else self.text

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------- splitting
def split_text(text: str, max_chars: int, overlap: int) -> list[tuple[int, str]]:
    """Split on paragraph / line / sentence boundaries into pieces <= max_chars.
    Returns (start_offset, piece) pairs; consecutive pieces overlap by about `overlap` chars."""
    text = text.strip()
    if len(text) <= max_chars:
        return [(0, text)] if text else []
    pieces, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind("\n\n"), window.rfind("\n"), window.rfind(". "))
            if cut > max_chars // 2:
                end = start + cut + 1
        pieces.append((start, text[start:end].strip()))
        if end >= len(text):
            break
        nxt = max(end - overlap, start + 1)
        # begin the overlap at a word boundary
        space = text.find(" ", nxt)
        start = space + 1 if 0 <= space < end else nxt
    return [(s, p) for s, p in pieces if p]


# Minimum share of word-like tokens per chunk. SOFI chart pages extract as bare number soup and
# are dropped; 10-K financial tables and data-sheet ordering tables (PIDs, specs) must be kept.
MIN_WORD_SHARE = {"sofi": 0.35, "clinical_lit": 0.30, "sec_filings": 0.15, "tech_docs": 0.0}


def is_mostly_prose(text: str, min_share: float = 0.35) -> bool:
    tokens = text.split()
    if len(tokens) < 12:
        return False
    wordy = sum(1 for t in tokens if re.fullmatch(r"[A-Za-z][A-Za-z\-'’]+[.,;:]?", t))
    return wordy / len(tokens) >= min_share


# ---------------------------------------------------------------- section detectors
_SEC_ITEM = re.compile(r"^\s*item\s+(\d{1,2}[a-c]?)\s*[.:]?\s*(.{0,100})$", re.I | re.M)
_SEC_ITEM_NAMES = {
    "1": "Business", "1A": "Risk Factors", "1B": "Unresolved Staff Comments", "1C": "Cybersecurity",
    "2": "Properties", "3": "Legal Proceedings", "4": "Mine Safety Disclosures",
    "5": "Market for Registrant's Common Equity", "6": "[Reserved]",
    "7": "Management's Discussion and Analysis (MD&A)", "7A": "Quantitative and Qualitative Disclosures About Market Risk",
    "8": "Financial Statements and Supplementary Data", "9": "Changes in and Disagreements with Accountants",
    "9A": "Controls and Procedures", "9B": "Other Information", "9C": "Foreign Jurisdictions that Prevent Inspections",
    "10": "Directors, Executive Officers and Corporate Governance", "11": "Executive Compensation",
    "12": "Security Ownership", "13": "Certain Relationships and Related Transactions",
    "14": "Principal Accountant Fees and Services", "15": "Exhibits and Financial Statement Schedules",
    "16": "Form 10-K Summary",
}


def sec_item_label(code: str) -> str:
    code = code.upper()
    return f"Item {code}. {_SEC_ITEM_NAMES.get(code, '')}".strip()


def _sec_headings(page_text: str) -> list[tuple[int, str]]:
    hits = list(_SEC_ITEM.finditer(page_text))
    if len(hits) >= 6:  # table of contents page
        return []
    return [(m.start(), sec_item_label(m.group(1))) for m in hits if m.group(1).upper() in _SEC_ITEM_NAMES]


_SOFI_CHAPTER = re.compile(r"^(CHAPTER \d+|ANNEX \d+[A-Z]?)\s+([A-Z][^\n]{3,120})$", re.M)
_SOFI_PART = re.compile(r"^(FOREWORD|KEY MESSAGES|EXECUTIVE SUMMARY|GLOSSARY|ACKNOWLEDGEMENTS|NOTES)\s*$", re.M)
_SOFI_RUNNING_HEAD = re.compile(r"^THE STATE OF FOOD SECURITY AND NUTRITION IN THE WORLD \d{4}\s*$", re.M)


def _sofi_headings(page_text: str) -> list[tuple[int, str]]:
    if len(_SOFI_CHAPTER.findall(page_text)) >= 4:  # contents page
        return []
    head = page_text[:400]
    m = _SOFI_CHAPTER.search(head) or _SOFI_PART.search(head)
    if not m:
        return []
    label = " ".join(m.group(0).split())
    return [(0, label.capitalize() if label.isupper() else label)]


_PAPER_SECTION = re.compile(r"^((?:[IVX]{1,5})\.[ \t]+[A-Z][A-Za-z ,&\-/]{2,80}|Abstract|ABSTRACT|REFERENCES|References|Conclusion|CONCLUSION)[ \t]*$", re.M)


def _paper_label(raw: str) -> str:
    numeral, _, title = raw.strip().partition(". ")
    if title and re.fullmatch(r"[IVX]{1,5}", numeral):
        return f"{numeral}. {title.strip().capitalize() if title.isupper() else title.strip()}"
    return raw.strip().capitalize()


def _paper_headings(page_text: str) -> list[tuple[int, str]]:
    return [(m.start(), _paper_label(m.group(1))) for m in _PAPER_SECTION.finditer(page_text)]


_DATASHEET_TABLE = re.compile(r"^(Table \d+\.[ \t]+[^\n]{3,100})$", re.M)
_CISCO_FOOTER = re.compile(r"©\s*\d{4} Cisco and/or its affiliates\. All rights reserved\.\s*(Page \d+ of \d+)?\s*-?")


def _datasheet_headings(page_text: str) -> list[tuple[int, str]]:
    return [(m.start(), m.group(1).strip()) for m in _DATASHEET_TABLE.finditer(page_text)]


HEADING_DETECTORS = {
    "sec_filings": _sec_headings,
    "sofi": _sofi_headings,
    "clinical_lit": _paper_headings,
    "tech_docs": _datasheet_headings,
}


# ---------------------------------------------------------------- chunkers
def _base_meta(src: Source) -> dict:
    meta = {k: v for k, v in src.meta.items() if k != "cover_name"}
    meta["doc_title"] = src.title
    return meta


def chunk_pdf(src: Source, pages: list[str], max_chars: int, overlap: int) -> list[Chunk]:
    detect = HEADING_DETECTORS.get(src.collection, lambda _t: [])
    chunks: list[Chunk] = []
    section: str | None = None
    for pno, page_text in enumerate(pages, start=1):
        if src.collection == "sofi":
            page_text = _SOFI_RUNNING_HEAD.sub("", page_text).strip()
        elif src.collection == "tech_docs":
            page_text = _CISCO_FOOTER.sub("", page_text).strip()
        headings = detect(page_text)
        for start, piece in split_text(page_text, max_chars, overlap):
            for pos, label in headings:
                if pos <= start + 40:
                    section = label
            if not is_mostly_prose(piece, MIN_WORD_SHARE.get(src.collection, 0.35)):
                continue
            chunks.append(Chunk(f"{src.source_id}:p{pno}:{start}", src.source_id, src.collection,
                                piece, page=pno, section=section, meta=_base_meta(src)))
        if headings:  # a heading late on the page applies to the next page
            section = headings[-1][1]
    return chunks


def chunk_html(src: Source, text: str, max_chars: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    lines = text.split("\n")
    sections: list[tuple[str | None, list[str]]] = [(None, [])]
    for line in lines[1:]:  # line 0 is the page <title>
        if line.startswith("### "):
            sections.append((line[4:].strip(), []))
        else:
            sections[-1][1].append(line)
    for idx, (heading, body) in enumerate(sections):
        body_text = "\n".join(body).strip()
        for start, piece in split_text(body_text, max_chars, overlap):
            if len(piece.split()) < 8:
                continue
            chunks.append(Chunk(f"{src.source_id}:s{idx}:{start}", src.source_id, src.collection,
                                piece, page=None, section=heading, meta=_base_meta(src)))
    return chunks
