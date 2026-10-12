# VERIFY

How to prove this project works, following the verification-skill approach: run the real user path, capture proof, check side effects, clean up. **Any step not yet executed is a draft.**

Synthetic data only. Run from the repo root.

## Launch

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

## Health check

Schema imports and every label validates against it:

```bash
PYTHONPATH=src python - <<'PY'
import glob, json
from dealdoc.schema import DocRecord
files = glob.glob("data/labels/*/*.json")
n = sum(1 for f in files for l in json.load(open(f))["labels"] if DocRecord.model_validate(l))
print(f"{len(files)} label files, {n} records valid")
PY
```

Expected: `40 label files, 137 records valid`.

## One end-to-end run

Regenerate the dataset from the fixed seed and confirm it is byte-identical:

```bash
python generator/make_scenarios.py   # expect Split: {'dev': 12, 'test': 28}
python generator/render_threads.py   # expect "Rendered threads + labels_A for all scenarios"
(cd data && sha256sum -c SCENARIOS.sha256 --quiet) && echo HASH_OK
git status --short data/             # expect no changes
```

**Planned, not yet executable:** run the Extractor → Resolver → Summarizer pipeline (Google ADK, Gemini Flash) on the 12 dev threads and score output against `data/labels/dev/`.

## Evidence

Save output from each run under `runs/<date>/` (gitignored): command log, the split line, `HASH_OK`, the validation count, and `git status` output.

**Planned, not yet executable:** per-thread predictions JSON and the accuracy report (type / holder / status / date accuracy).

## Side-effect checks

- Today: the generator writes only to `data/scenarios`, `data/threads`, `data/labels`, and `data/SCENARIOS.sha256`. `git status` shows no other changes.
- Thread counts: `ls data/threads/dev | wc -l` → 12, `ls data/threads/test | wc -l` → 28.
- **Planned, not yet executable:** after the Salesforce sync (simple-salesforce), query the Developer Edition org and confirm one `Deal_Document__c` per extracted document, linked to the right Opportunity, with matching holder and status fields. Seeing the API call succeed doesn't count; the records have to be in the org.

## Cleanup

```bash
git checkout -- data/ && git clean -fd data/   # undo any data drift
rm -rf .venv runs/
```

**Planned, not yet executable:** delete test `Deal_Document__c` records and test Opportunities from the dev org, then re-query to confirm zero remain.
