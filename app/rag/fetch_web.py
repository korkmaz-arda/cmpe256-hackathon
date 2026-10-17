"""Download the professor's public sources; run with python -m app.rag.fetch_web."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [('DataSource-Cisco.txt', 'technology', 'Cisco'),
           ('Agilent.txt', 'clinical', 'Agilent'),
           ('Google GCP.txt', 'technology', 'Google Cloud')]


def clean_url(url: str) -> str:
    parts = urlsplit(url.rstrip('.,;)'))
    query = [(k, v) for k, v in parse_qsl(parts.query) if not
             (k.startswith('utm_') or k in {'_gl', '_ga', 'gclid', 'fbclid'})]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ''))


def main() -> None:
    output = ROOT / 'data/web'
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / 'manifest.json'
    old = {row['url']: row for row in json.loads(manifest_path.read_text())} if manifest_path.exists() else {}
    session = requests.Session()
    session.headers['User-Agent'] = 'Mozilla/5.0 (compatible; CourseKnowledgeFetcher/1.0)'
    for scheme in ('https://', 'http://'):
        session.mount(scheme, HTTPAdapter(max_retries=Retry(total=2, backoff_factor=1,
                      status_forcelist=[429, 500, 502, 503, 504])))
    records = []
    for filename, domain, vendor in SOURCES:
        urls = dict.fromkeys(clean_url(u) for u in re.findall(r'https?://[^\s<>"\']+', (ROOT / 'sources' / filename).read_text()))
        for url in urls:
            pdf = urlsplit(url).path.lower().endswith('.pdf')
            kind = 'pdf' if pdf else 'html'
            source = 'Google Cloud docs' if vendor == 'Google Cloud' else vendor + (' datasheet' if pdf else ' product page')
            stem = re.sub(r'[^a-zA-Z0-9_-]', '-', urlsplit(url).path.rstrip('/').split('/')[-1])[:100]
            path = output / domain / (stem + '-' + hashlib.sha256(url.encode()).hexdigest()[:10] + ('.pdf' if pdf else '.txt'))
            row = dict(domain=domain, source=source, title=stem, url=url,
                       path=str(path.relative_to(ROOT)), type=kind, ok=False, error=None)
            if old.get(url, {}).get('ok') and path.exists() and path.stat().st_size:
                records.append(old[url])
                print('SKIP', url)
                continue
            try:
                response = session.get(url, timeout=(15, 60))
                response.raise_for_status()
                path.parent.mkdir(parents=True, exist_ok=True)
                if pdf:
                    if not response.content.startswith(b'%PDF'):
                        raise ValueError('Expected PDF but received another content type')
                    path.write_bytes(response.content)
                else:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    row['title'] = soup.title.get_text(' ', strip=True) if soup.title else stem
                    for tag in soup(['nav', 'script', 'style', 'footer', 'header', 'noscript']):
                        tag.decompose()
                    body = soup.find('main') or soup.body or soup
                    content = '\n'.join(line.strip() for line in body.get_text('\n', strip=True).splitlines() if line.strip())
                    if len(content) < 100 or 'Access Denied' in row['title']:
                        raise ValueError('Page has no readable content or access was denied')
                    path.write_text(content, encoding='utf-8')
                row['ok'] = True
                print('OK', url)
            except Exception as exc:
                row['error'] = str(exc)
                print('FAILED', url, str(exc))
            records.append(row)
            manifest_path.write_text(json.dumps(records, indent=2), encoding='utf-8')
    manifest_path.write_text(json.dumps(records, indent=2), encoding='utf-8')
    print('Downloaded: %d; failed: %d' % (sum(r['ok'] for r in records), sum(not r['ok'] for r in records)))


if __name__ == '__main__':
    main()
