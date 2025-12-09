# Stories Data Pipeline

The worker CLI under `app/workers/run_pipeline.py` orchestrates a small DAG of
steps using the in-repo `dagmatic` helper. Each successful step writes its
status into a shared manifest at `data/pipeline_manifest.json`. When the
pipeline runs again, steps that already have an entry in the manifest are
skipped unless you pass `--force`.

## Usage

```bash
python -m app.workers.run_pipeline describe
python -m app.workers.run_pipeline run              # run every step once
python -m app.workers.run_pipeline run step3a_fetch_episodes
python -m app.workers.run_pipeline run step3a_fetch_episodes --force
```

The manifest tracks the most recent `run_id`, timestamp, optional message, and
extra details returned by each step. If you need to invalidate a step manually,
delete its entry from `data/pipeline_manifest.json` or use `--force` for the
next run.
