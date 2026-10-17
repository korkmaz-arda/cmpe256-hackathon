"""Source-backed, deterministic product search without an embedding service."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

CATALOG_DIR = Path(__file__).resolve().parents[1] / 'catalog'
STOP_WORDS = set('a an and are as at be by for from in is it of on or the to with need needs'.split())


def _tokens(text: str) -> List[str]:
    return [t for t in re.findall(r'[a-z0-9]+', text.lower()) if t not in STOP_WORDS]


def _render(entry: Dict[str, Any]) -> str:
    # Provenance and IDs should not influence lexical relevance.
    fields = {k: v for k, v in entry.items() if k not in {'id', 'source_url', 'source_pages'}}
    if fields.get('sd_wan'):
        fields['sd_wan'] = 'SD-WAN software defined WAN'
    if fields.get('power_supply_redundancy'):
        fields['power_supply_redundancy'] = 'redundant power supplies redundancy'
    return ' '.join(str(v) for v in fields.values() if v is not None)


def _adjust(entry: Dict[str, Any], constraints: Dict[str, Any], catalog: str):
    adjustment, reasons = 0.0, []

    def add(value, reason):
        nonlocal adjustment
        adjustment += value
        reasons.append('%+.2f %s' % (value, reason))

    deployment = constraints.get('deployment', '').lower()
    if deployment and catalog == 'cisco':
        if deployment == 'cloud':
            virtual = entry['form_factor'] == 'virtual'
            add(0.4 if virtual else -0.2, 'cloud deployment: virtual' if virtual else 'cloud deployment: physical')
        else:
            fits = deployment in (entry.get('deployment') or '').lower()
            add(0.2 if fits else -0.1, 'deployment match' if fits else 'deployment mismatch')
    if constraints.get('needs_redundancy') and catalog == 'cisco':
        redundancy = entry.get('power_supply_redundancy')
        add(0.25 if redundancy is True else -0.15 if redundancy is False else -0.05,
            'redundant PSU documented' if redundancy is True else 'redundant PSU absent or unknown')
    if 'throughput_gbps' in constraints and catalog == 'cisco':
        # Only examine forwarding/aggregate performance, never interface line rates.
        text = entry.get('max_throughput_text') or ''
        values = [float(n) / (1000 if unit.lower() == 'mbps' else 1)
                  for n, unit in re.findall(r'(\d+(?:\.\d+)?)\s*(Gbps|Mbps)', text, re.I)]
        if values:
            meets = max(values) >= constraints['throughput_gbps']
            add(0.2 if meets else -0.3, 'published maximum meets throughput' if meets else 'published maximum below throughput')
        else:
            add(-0.05, 'throughput unknown')
    if constraints.get('budget', '').lower() == 'low' and catalog == 'cisco':
        model = entry.get('model') or ''
        if entry['family'] == 'Catalyst 8200' or model in {'ISR4221', 'ISR4221X', 'ISR4321'}:
            add(0.15, 'smaller branch platform budget heuristic; no price data')
        elif entry['family'] == 'ASR 1000':
            add(-0.15, 'aggregation platform budget heuristic; no price data')
    regulatory = constraints.get('regulatory', '').upper()
    if regulatory and catalog == 'agilent':
        known = entry.get('regulatory')
        add(0.35 if known and known.upper() == regulatory else -0.35 if known else -0.15,
            'regulatory match' if known and known.upper() == regulatory else 'regulatory mismatch or unknown')
    return adjustment, reasons


def recommend_products(catalog: str, requirements: str,
                       constraints: Optional[dict] = None, k: int = 3) -> List[dict]:
    """Rank a catalog by NumPy TF-IDF cosine similarity plus explicit context.

    TF uses raw counts and IDF=log((1+N)/(1+document_frequency))+1, fitted
    only on catalog entries; query-only words are ignored. Ties sort by ID.
    Context rules (additive, soft preferences, never hard eligibility filters):
    * Cisco deployment=cloud: virtual +.40, physical -.20. Other deployment:
      substring match +.20, mismatch -.10.
    * Cisco needs_redundancy=true: documented redundant PSU +.25, false -.15,
      unknown -.05. Virtual infrastructure redundancy is not inferred.
    * Cisco throughput_gbps: greatest published forwarding/aggregate number
      meets requested value +.20, below -.30, unknown -.05. License, mode,
      packet size and CEF-only qualifications still apply; this is not an
      IPsec or guaranteed production-capacity test.
    * Cisco budget=low: Catalyst 8200 or ISR4221/4221X/4321 +.15; ASR1000
      -.15; others zero. This size heuristic makes no claim about prices.
    * Agilent regulatory: exact case-insensitive label +.35, known mismatch
      -.35, unknown -.15; unknown status does not establish approval.
    No rules are inferred from free text. Unsupported constraint keys raise
    ValueError. Empty/unmatched queries have zero lexical similarity; explicit
    constraints can still rank them. Scores are unbounded relevance values,
    not probabilities. Returned explanations disclose all applied adjustments.
    """
    if catalog not in {'cisco', 'agilent'}:
        raise ValueError('catalog must be cisco or agilent')
    if not isinstance(requirements, str):
        raise ValueError('requirements must be a string')
    if isinstance(k, bool) or not isinstance(k, int) or k < 0:
        raise ValueError('k must be a nonnegative integer')
    constraints = {} if constraints is None else constraints
    if not isinstance(constraints, dict):
        raise ValueError('constraints must be a dictionary')
    allowed = {'deployment', 'needs_redundancy', 'throughput_gbps', 'budget'} if catalog == 'cisco' else {'regulatory'}
    if set(constraints) - allowed:
        raise ValueError('Unsupported constraints: ' + ', '.join(sorted(set(constraints) - allowed)))
    for key, value in constraints.items():
        if key == 'needs_redundancy':
            if not isinstance(value, bool):
                raise ValueError('needs_redundancy must be boolean')
        elif key == 'throughput_gbps':
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('throughput_gbps must be finite and nonnegative')
        elif not isinstance(value, str):
            raise ValueError(key + ' must be a string')
    filename = 'cisco_routers.json' if catalog == 'cisco' else 'agilent_products.json'
    entries = json.loads((CATALOG_DIR / filename).read_text(encoding='utf-8'))
    if not entries or k == 0:
        return []
    counts = [Counter(_tokens(_render(entry))) for entry in entries]
    vocabulary = sorted(set().union(*(set(c) for c in counts)))
    idf = np.array([math.log((1 + len(entries)) / (1 + sum(term in c for c in counts))) + 1
                    for term in vocabulary])
    matrix = np.array([[c[t] for t in vocabulary] for c in counts], dtype=float) * idf
    query_counts = Counter(_tokens(requirements))
    query = np.array([query_counts[t] for t in vocabulary], dtype=float) * idf
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query)
    similarities = np.divide(np.sum(matrix * query, axis=1), norms, out=np.zeros(len(entries)), where=norms > 0)
    results = []
    for i, entry in enumerate(entries):
        adjustment, reasons = _adjust(entry, constraints, catalog)
        overlaps = [(vocabulary[j], float(matrix[i, j] * query[j]))
                    for j in range(len(vocabulary)) if matrix[i, j] and query[j]]
        matched = [t for t, _ in sorted(overlaps, key=lambda pair: (-pair[1], pair[0]))[:6]]
        name = entry.get('model') or entry.get('name') or entry['family']
        why = ('Matches ' + ', '.join(matched) if matched else 'No overlapping catalog terms')
        if reasons:
            why += '; ' + '; '.join(reasons)
        results.append(dict(id=entry['id'], name=name, model=entry.get('model'),
                            similarity=float(similarities[i]), context_adjustment=adjustment,
                            final_score=float(similarities[i]) + adjustment,
                            matched_terms=matched, why=why + '.', source_url=entry['source_url']))
    return sorted(results, key=lambda row: (-row['final_score'], row['id']))[:k]


TOOL_SPEC = {
    'type': 'function',
    'function': {
        'name': 'recommend_products',
        'description': 'Search source-backed Cisco or Agilent catalogs with TF-IDF and explained soft constraints.',
        'parameters': {
            'type': 'object',
            'properties': {
                'catalog': {'type': 'string', 'enum': ['cisco', 'agilent']},
                'requirements': {'type': 'string'},
                'constraints': {'type': ['object', 'null'], 'properties': {
                    'deployment': {'type': 'string'},
                    'needs_redundancy': {'type': 'boolean'},
                    'throughput_gbps': {'type': 'number', 'minimum': 0},
                    'budget': {'type': 'string'},
                    'regulatory': {'type': 'string'}}, 'additionalProperties': False},
                'k': {'type': 'integer', 'minimum': 0, 'default': 3}},
            'required': ['catalog', 'requirements'], 'additionalProperties': False}}}


if __name__ == '__main__':
    for kind, query, context in [
        ('cisco', 'branch office router with SD-WAN, intermittent connectivity, need redundant power',
         {'deployment': 'branch', 'needs_redundancy': True}),
        ('agilent', 'measure mitochondrial respiration in PBMCs for a diabetes trial', None),
    ]:
        print(json.dumps(recommend_products(kind, query, context), indent=2))
