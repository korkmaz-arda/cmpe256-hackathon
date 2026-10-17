# Product catalogs

Run from the project root with Python 3.9:

```sh
.venv/bin/python -m app.rag.fetch_web
.venv/bin/python -m app.tools.product_recommender
.venv/bin/python tests/test_product_recommender.py
```

## Source collection

`fetch_web` reads only HTTP(S) links from the three supplied source lists,
removes common tracking parameters, retries transient HTTP failures, and writes
readable HTML text or original PDFs to `data/web/`. The manifest records each
URL, local path, type, title, and download outcome. Successful existing files
are skipped on subsequent runs; failed requests are retried. Cisco product
pages are collected before datasheets, so their text is available as fallback
when a datasheet fails. Catalog facts are never silently substituted from a
product page for PDF facts.

The initial run downloaded all ten Cisco sources and three Google Cloud
sources. All six Agilent URLs returned HTTP 403, including retries with a full
browser User-Agent. Those failures remain visible in the manifest:

- https://www.agilent.com/en/product/cell-analysis/real-time-cell-metabolic-analysis
- https://www.agilent.com/about/newsroom/presrel/2023/07mar-ca23010.html
- https://www.agilent.com/en/product/digital-pathology
- https://www.agilent.com/en/product/digital-pathology/digital-pathology-scanners
- https://www.agilent.com/en/product/digital-pathology/digital-pathology-scanners/nanozoomer-slide-scanner-system-4370282
- https://www.agilent.com/en/product/special-stains

Agilent catalog entries were manually verified through the browser search
reader's accessible copies of the supplied pages. They are not represented as
successful local downloads. The supplied metabolic-analysis category page
supports 2D/3D cell models; its linked press release supports respiration,
glycolysis, ATP production, therapeutic development and toxicity programs.
NanoZoomer's product page explicitly states IVD. Regulatory status for Seahorse
and Artisan is null because the consulted pages do not state a label. No PBMC,
diabetes-trial validation, or diagnostic approval is inferred.

## Cisco transcription

The 29 entries comprise five family summaries and 24 model entries. PDF pages
were extracted using `pypdf.PdfReader(...).pages[n].extract_text()` and manually
transcribed with 1-based PDF page references in `source_pages`. Null means the
field was not established by the consulted text; an empty parts list means no
compatible parts were transcribed, not that the product has none.

- Catalyst 8300: pages 3–7 (features, models, throughput), 10 (wireless and
  survivability), 15–17 (memory, fan trays, power supplies).
- Catalyst 8200: pages 3, 5–6 (platform and performance), 12–13 (memory,
  serial NIMs, power). The external PoE PSU is not labeled redundant power.
- Catalyst 8000V: pages 5–6, 9–12 (deployment, features, VM configuration,
  interfaces). VM configurations are not separate hardware models.
- ISR 4000: pages 4–5, 9, 24–25 (branch features, model tables, licensing,
  ordering). Table 8's CEF-only IMIX boost results are explicitly labeled;
  they differ from the general Table 5 boost row. Per-model IPsec performance
  is unknown. Redundant PSU support is explicitly established for 4461,
  4451 and 4431; other models retain null.
- ASR 1000: pages 3–5, 9, 12–14, 27–29. Model interfaces use the chassis
  specification table rather than conflicting HX port counts in ordering
  descriptions. Family-level processor/interface parts are not asserted to
  fit every chassis. Modular chassis throughput is left null rather than
  copying the family maximum onto every model.

Parts are selected PIDs from supported-module, accessory, PSU specification,
and ordering tables; they are not an exhaustive compatibility or service guide.
Family summaries and model entries are both searchable and may both appear
in results. `best_for` is a short synthesis of stated deployment descriptions.
SD-WAN support does not imply every license, release, module, or mode supports
all features simultaneously.

## Recommender

No API key, embeddings or scikit-learn are required. NumPy TF-IDF uses catalog
entries as documents, then cosine similarity against the requirement text.
The function docstring documents every context adjustment. Each result includes
lexical similarity, additive context adjustment, final score, overlapping terms,
a one-sentence explanation, and source URL. Constraints are soft ranking
preferences; a result is not a procurement or regulatory eligibility decision.
Throughput comparisons use the greatest explicitly transcribed forwarding or
aggregate number; mode, traffic profile and license qualifications still apply.
The low-budget rule is a platform-size heuristic with no pricing evidence.
`TOOL_SPEC` uses the OpenAI Chat Completions function-tool schema; pass JSON
arguments to `recommend_products(**arguments)`.
