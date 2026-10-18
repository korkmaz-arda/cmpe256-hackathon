"""Grounding consistency: the manifest, the official link lists, the files on disk and the agent prompts agree."""
from __future__ import annotations

import re

import pytest

from consultai.agents.registry import specialists
from consultai.config import RESOURCES_DIR
from consultai.ingest.sources import ALL_SOURCES, KNOWN_GAPS, sources_for


def test_every_manifest_source_exists():
    missing = [s.source_id for s in ALL_SOURCES if not s.local_path.exists()]
    assert not missing, f"missing files (run scripts/setup_data.py): {missing}"


@pytest.mark.parametrize("site,listfile", [("cisco", "DataSource-Cisco.txt"), ("gcp", "Google GCP.txt"),
                                           ("agilent", "Agilent.txt")])
def test_web_sources_match_official_link_lists(site, listfile):
    official = set(re.findall(r"https?://\S+", (RESOURCES_DIR / "documents" / listfile).read_text()))
    official = {u.split("?")[0] for u in official}
    ours = {s.citation_url for s in ALL_SOURCES if f"web/{site}/" in s.path}
    assert ours <= official, f"URLs not in {listfile}: {ours - official}"


@pytest.mark.parametrize("site", ["cisco", "gcp"])
def test_web_sources_match_sources_tsv(site):
    rows = dict(line.split("\t") for line in (RESOURCES_DIR / "web" / site / "sources.tsv").read_text().splitlines() if line)
    for s in ALL_SOURCES:
        if f"web/{site}/" in s.path:
            fname = s.path.rsplit("/", 1)[1]
            assert rows[fname].split("?")[0] == s.citation_url


def test_agilent_saved_pages_map_to_canonical_urls():
    for s in sources_for("clinical"):
        if s.kind != "html":
            continue
        html = s.local_path.read_text(errors="ignore")
        canon = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', html)
        if canon:  # the 2023 press release has no canonical link; it is matched by title
            assert canon.group(1) == s.citation_url


@pytest.mark.parametrize("name", ["technology", "clinical", "sec", "csr"])
def test_prompt_lists_exactly_the_manifest_sources_and_gaps(name):
    agent = specialists()[name]
    prompt = agent.system_prompt()
    assert "{{" not in prompt
    listed = set(re.findall(r"- `([a-z0-9][^`]+)`: ", prompt.split("## Tools")[0]))
    assert listed == {s.source_id for s in sources_for(name)}
    for gap in KNOWN_GAPS[name]:
        assert gap in prompt
    for heading in ("## Identity / persona", "## Do", "## Don't", "## Grounding sources", "## Tools",
                    "Evidence and uncertainty policy", "## Output contract"):
        assert heading in prompt, f"{name} prompt lacks {heading}"


def test_no_ibm_source_and_gap_is_declared():
    assert not any("ibm" in s.source_id.lower() or "IBM" in s.title for s in ALL_SOURCES)
    assert any("IBM" in g for g in KNOWN_GAPS["technology"])
