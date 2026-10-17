#!/usr/bin/env bash
# Build the Canvas submission zip: all source code, prompts, catalogs, eval results and docs.
# Excludes secrets (.env), the virtualenv, course data and generated indexes.
set -euo pipefail
cd "$(dirname "$0")/.."
out="${1:-cmpe256_hackathon_submission.zip}"
rm -f "$out"
git ls-files -z | xargs -0 zip -q "$out"
echo "Wrote $out ($(du -h "$out" | cut -f1)), $(unzip -l "$out" | tail -1 | awk '{print $2}') files"
unzip -l "$out" | grep -E "\.env$" && { echo "ERROR: .env in zip"; exit 1; } || true
