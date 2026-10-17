"""Local ClinicalTrials.gov search tools; no network or API key required."""
from __future__ import annotations

import csv
import json
import re
import threading
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'index' / 'trials.pkl'
FILES = {
    'covid': 'ctg-studies_covid.csv',
    'diabetes': 'ctg-studies_diabetes.csv',
    'heart_attack': 'ctg-studies_Hearattack.csv',
    'knee_injuries': 'ctg-studies_KneeInjuries.csv',
}
TEXT_COLUMNS = ['Study Title', 'Conditions', 'Interventions', 'Brief Summary',
                'Primary Outcome Measures', 'Secondary Outcome Measures',
                'Other Outcome Measures']
_FRAME = None
_INDEXES = {}
_LOCK = threading.RLock()
_TOKEN = re.compile(r'[a-z0-9]+')


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _load() -> pd.DataFrame:
    """Load once, invalidating the compressed pickle when source CSVs change."""
    global _FRAME
    with _LOCK:
        if _FRAME is not None:
            return _FRAME
        sources = {name: ROOT / 'data' / 'Clinical' / file for name, file in FILES.items()}
        signature = [(name, p.stat().st_size, p.stat().st_mtime_ns)
                     for name, p in sources.items()]
        if CACHE.exists():
            try:
                frame = pd.read_pickle(CACHE, compression='gzip')
                if frame.attrs.get('source_signature') == signature:
                    _FRAME = frame
                    return frame
            except (OSError, ValueError, EOFError):
                pass  # A partial or obsolete cache can safely be rebuilt from CSVs.
        csv.field_size_limit(2**31 - 1)
        frames = []
        for name, path in sources.items():
            frame = pd.read_csv(path, dtype=str, keep_default_na=False, engine='python')
            frame['dataset'] = name
            frames.append(frame)
        frame = pd.concat(frames, ignore_index=True)
        frame.attrs['source_signature'] = signature
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        temporary = CACHE.with_suffix('.pkl.tmp')
        frame.to_pickle(temporary, compression={'method': 'gzip', 'compresslevel': 1})
        temporary.replace(CACHE)
        _FRAME = frame
        return frame


def _validate_dataset(dataset: Optional[str]) -> None:
    if dataset is not None and dataset not in FILES:
        raise ValueError('dataset must be one of: ' + ', '.join(FILES))


def _index(dataset: Optional[str]):
    _validate_dataset(dataset)
    with _LOCK:
        if dataset not in _INDEXES:
            frame = _load()
            if dataset is not None:
                frame = frame[frame['dataset'] == dataset]
            texts = frame[TEXT_COLUMNS].agg('\n'.join, axis=1).tolist()
            corpus = [_tokens(text) or ['_empty_'] for text in texts]
            _INDEXES[dataset] = (frame, texts, BM25Okapi(corpus))
        return _INDEXES[dataset]


def _snippet(text: str, terms: list[str]) -> str:
    """Choose the 300-character window with the most query-token matches."""
    matches = list(re.finditer(r'\b(?:' + '|'.join(map(re.escape, set(terms))) + r')\b',
                               text, re.IGNORECASE)) if terms else []
    starts = {max(0, m.start() - 70) for m in matches} or {0}
    start = max(sorted(starts), key=lambda s: sum(s <= m.start() < s + 300 for m in matches))
    return re.sub(r'\s+', ' ', text[start:start + 300]).strip()


def search_trials(query: str, dataset: Optional[str] = None,
                  status: Optional[str] = None, k: int = 5) -> list[dict]:
    """Rank matching studies with BM25; status matching is exact, case-insensitive."""
    if not isinstance(k, int) or isinstance(k, bool) or k < 0:
        raise ValueError('k must be a nonnegative integer')
    _validate_dataset(dataset)
    terms = _tokens(query)
    if not terms or k == 0:
        return []
    frame, texts, bm25 = _index(dataset)
    scores = bm25.get_scores(terms)
    eligible = np.array([bool(set(terms).intersection(_tokens(text))) for text in texts])
    if status is not None:
        eligible &= frame['Study Status'].str.casefold().eq(status.strip().casefold()).to_numpy()
    positions = np.flatnonzero(eligible)
    positions = positions[np.argsort(-scores[positions], kind='stable')[:k]]
    results = []
    for pos in positions:
        row = frame.iloc[int(pos)]
        results.append(dict(nct_id=row['NCT Number'], title=row['Study Title'],
                            url=row['Study URL'], status=row['Study Status'],
                            phases=row['Phases'], enrollment=row['Enrollment'],
                            sponsor=row['Sponsor'], conditions=row['Conditions'],
                            snippet=_snippet(texts[int(pos)], terms), score=float(scores[pos])))
    return results


def instrument_usage(instrument: str = 'seahorse') -> dict:
    """Find literal instrument mentions with boundaries, including Seahorse aliases."""
    name = instrument.strip()
    if not name:
        raise ValueError('instrument must not be empty')
    pattern = (r'\b(?:seahorse|xf(?:e)?\s*[- ]?\d*\s+analy[sz]er|xfe?\s*[- ]?96)\b'
               if name.casefold() == 'seahorse' else r'\b' + re.escape(name) + r'\b')
    matcher = re.compile(pattern, re.IGNORECASE)
    frame = _load()
    trials = []
    statuses = {}
    counts = dict.fromkeys(FILES, 0)
    # Outcome measures come first so the evidence describes the measurement when possible.
    columns = TEXT_COLUMNS[4:] + TEXT_COLUMNS[:4]
    for _, row in frame.iterrows():
        measurement = None
        for column in columns:
            text = row[column]
            match = matcher.search(text)
            if match:
                sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
                measurement = next(s.strip() for s in sentences if matcher.search(s))
                break
        if measurement is None:
            continue
        counts[row['dataset']] += 1
        status = row['Study Status']
        statuses[status] = statuses.get(status, 0) + 1
        trials.append(dict(nct_id=row['NCT Number'], title=row['Study Title'],
                           url=row['Study URL'], dataset=row['dataset'],
                           measurement_sentence=measurement))
    return dict(instrument=name, total=len(trials), per_dataset=counts,
                per_status=statuses, trials=trials)


def dataset_stats() -> dict:
    """Counts describe CSV records, including studies appearing in multiple exports."""
    frame = _load()
    def counts(column):
        return {str(key): int(value) for key, value in frame[column].value_counts().items()}
    return dict(total=len(frame), by_dataset=counts('dataset'),
                by_status=counts('Study Status'), by_study_type=counts('Study Type'),
                by_results_availability=counts('Study Results'))


TOOL_SPECS = [
    {'type': 'function', 'function': {
        'name': 'search_trials', 'description': 'Search local ClinicalTrials.gov studies using BM25.',
        'parameters': {'type': 'object', 'properties': {
            'query': {'type': 'string'},
            'dataset': {'type': 'string', 'enum': list(FILES)},
            'status': {'type': 'string'},
            'k': {'type': 'integer', 'minimum': 0, 'default': 5}},
            'required': ['query'], 'additionalProperties': False}}},
    {'type': 'function', 'function': {
        'name': 'instrument_usage', 'description': 'Find instrument mentions and measurement evidence in trials.',
        'parameters': {'type': 'object', 'properties': {
            'instrument': {'type': 'string', 'default': 'seahorse'}},
            'additionalProperties': False}}},
]


def call_tool(name: str, args: dict):
    functions = {'search_trials': search_trials, 'instrument_usage': instrument_usage}
    if name not in functions:
        raise ValueError('Unknown trials tool: ' + name)
    return functions[name](**args)


if __name__ == '__main__':
    started = time.perf_counter()
    print(json.dumps(dataset_stats(), indent=2))
    print('Data load: {:.3f}s'.format(time.perf_counter() - started))
    print(json.dumps(instrument_usage('seahorse'), indent=2))
    started = time.perf_counter()
    print(json.dumps(search_trials('mitochondrial function PBMC', dataset='diabetes'), indent=2))
    print('Search including lazy index: {:.3f}s'.format(time.perf_counter() - started))
