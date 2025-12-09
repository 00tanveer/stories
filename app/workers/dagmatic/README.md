## Dagmatic quickstart

`dagmatic` is now intentionally tiny—everything lives inside `app/workers/dagmatic/__init__.py`.

### Core pieces

- **Step**: dataclass with a `name`, optional `depends_on`, and a `run` callable.
- **StepContext**: gives you the `run_id` plus a shared `params` dict you can mutate if steps need to pass lightweight state.
- **StepResult**: return `ok()` or `failed()` to tell the executor what happened; optionally include a `details` dict that the manifest will persist.
- **Dag / Executor**: wire steps together, apply a topological ordering, and run everything sequentially. Successful steps are recorded in `data/pipeline_manifest.json` and skipped on subsequent runs unless `force=True`.

### Minimal usage

```python
from app.workers import dagmatic


def say_hi(ctx: dagmatic.StepContext) -> dagmatic.StepResult:
    print(f"hello from {ctx.run_id}")
    return dagmatic.StepResult.ok("done")


def build_step() -> dagmatic.Step:
    return dagmatic.Step(name="example", run=say_hi)


pipeline = dagmatic.Dag([build_step()])
dagmatic.Executor(pipeline).run(run_id="manual-dev")

# force a re-run even if the manifest says the step already succeeded
dagmatic.Executor(pipeline).run(run_id="manual-dev", force=True)
```

That is the entire surface area—add structure only when we truly need it.
