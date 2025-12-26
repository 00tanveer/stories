"""Stories data pipeline CLI backed by the dagmatic mini-DAG."""

import uuid
from importlib import import_module
from typing import Iterable, Sequence, Tuple

import click

from app.workers import dagmatic

_STAGE_DEFS: Sequence[Tuple[str, str, Tuple[str, ...]]] = (
    ("step1_seed_podcast_list", "Step 1 • curate podcast list", ()),
    ("step2_load_podcasts", "Step 2 • load podcasts table", ("step1_seed_podcast_list",)),
    ("step3a_fetch_episodes", "Step 3a • fetch episode metadata", ("step1_seed_podcast_list",)),
    ("step3b_load_episodes", "Step 3b • load episodes table", ("step2_load_podcasts",)),
    ("step4a_generate_transcripts", "Step 4a • generate transcripts", ("step3b_load_episodes",)),
    ("step4b_load_transcripts", "Step 4b • load transcript tables", ("step4a_generate_transcripts",)),
    ("step5_classify_qa", "Step 5 • classify questions & answers", ("step4b_load_transcripts",)),
    ("step6_index_chroma", "Step 6 • index Chroma collections", ("step5_classify_qa",)),
    ("step7_index_elasticsearch", "Step 7 • build Elasticsearch index", ("step4b_load_transcripts",)),
)

def _placeholder(title: str):
    def _runner(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
        raise NotImplementedError(f"{title} is not implemented yet")

    return _runner

_CUSTOM_STEP_MODULES = {
    "step1_seed_podcast_list": "app.workers.steps.01_seed_podcast_list",
    "step2_load_podcasts": "app.workers.steps.02_load_podcasts",
    "step3a_fetch_episodes": "app.workers.steps.3a_fetch_episodes",
    "step3b_load_episodes": "app.workers.steps.3b_load_episodes",
    "step4a_generate_transcripts": "app.workers.steps.4a_generate_transcripts",
    "step4b_load_transcripts": "app.workers.steps.4b_load_transcripts",
    "step5_classify_qa": "app.workers.steps.05_classify_qa",
    "step6_index_chroma": "app.workers.steps.06_index_chroma",
    "step7_index_elasticsearch": "app.workers.steps.07_index_elasticsearch",
}


def _build_step(defn: Tuple[str, str, Tuple[str, ...]]) -> dagmatic.Step:
    name, title, deps = defn
    module_path = _CUSTOM_STEP_MODULES.get(name)
    if module_path:
        builder = getattr(import_module(module_path), "build_step", None)
        if builder is None:
            raise RuntimeError(f"Module '{module_path}' must expose build_step()")
        step = builder()
        if step.name != name or tuple(step.depends_on) != deps:
            raise RuntimeError(f"Step '{name}' metadata mismatch")
        step.description = step.description or title
        return step
    return dagmatic.Step(name=name, description=title, depends_on=deps, run=_placeholder(title))


_STEPS = [_build_step(defn) for defn in _STAGE_DEFS]
_PIPELINE = dagmatic.Dag(_STEPS)
_INDEX = {step.name: step for step in _STEPS}


@click.group()
def cli() -> None:
    """Orchestrate the Stories data pipeline."""


@cli.command("describe")
def describe() -> None:
    """List every step with its dependencies."""
    for step in _PIPELINE.steps():
        deps = ", ".join(step.depends_on) or "-"
        click.echo(f"{step.name}: {step.description} | deps: {deps}")


@cli.command("run")
@click.argument("targets", nargs=-1)
@click.option("--force", is_flag=True, help="Re-run steps even if cached in the manifest.")
@click.option(
    "--no-deps",
    is_flag=True,
    default=False,
    help="Run only the specified steps without auto-including dependencies.",
)
def run_cli(targets: Tuple[str, ...], force: bool, no_deps: bool) -> None:
    """Run the full DAG or the specified steps."""
    if no_deps:
        target_list = _validate_targets(targets)
    else:
        target_list = _expand_targets(targets) if targets else None
    run_id = f"manual-{uuid.uuid4().hex[:8]}"
    result = dagmatic.Executor(_PIPELINE).run(run_id=run_id, targets=target_list, force=force)
    _print_result(run_id, result)


def _expand_targets(names: Iterable[str]) -> list[str]:
    wanted: set[str] = set()
    stack = list(names)
    while stack:
        name = stack.pop()
        if name not in _INDEX:
            raise click.ClickException(f"Unknown step '{name}'")
        if name in wanted:
            continue
        wanted.add(name)
        stack.extend(_INDEX[name].depends_on)
    return [step.name for step in _PIPELINE.steps(selected=wanted)]


def _validate_targets(names: Iterable[str]) -> list[str]:
    validated: list[str] = []
    for name in names:
        if name not in _INDEX:
            raise click.ClickException(f"Unknown step '{name}'")
        validated.append(name)
    # Maintain DAG ordering for deterministic execution.
    ordered = [step.name for step in _PIPELINE.steps(selected=validated)]
    return ordered


def _print_result(run_id: str, result: dagmatic.DagRunResult) -> None:
    click.echo(f"run_id={run_id}")
    for label, data in (("succeeded", result.succeeded), ("skipped", result.skipped), ("failed", result.failed)):
        click.echo(f"  {label:<8}: {data}")


if __name__ == "__main__":
    cli()
