"""Pipeline step that loads episode metadata into Postgres."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.services.podcasts import save_episodes
from app.workers import dagmatic

METADATA_PATH = Path("data/podcasts/pod_episodes_metadata.json")


def build_step() -> dagmatic.Step:
    """Return the dagmatic step used for loading episode metadata."""

    return dagmatic.Step(
        name="step3b_load_episodes",
        description="Step 3b - load episode metadata into Postgres",
        depends_on=("step2b_load_podcasts",),
        run=_run,
    )


def _run(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
    """Persist episode metadata into the episodes table."""

    if not METADATA_PATH.exists():
        return dagmatic.StepResult.failed(f"Missing episode metadata at {METADATA_PATH}")

    try:
        with METADATA_PATH.open("r", encoding="utf-8") as handle:
            episodes = json.load(handle)
    except json.JSONDecodeError as exc:
        return dagmatic.StepResult.failed(f"Invalid JSON in {METADATA_PATH}: {exc}")

    if not episodes:
        return dagmatic.StepResult.failed("Episode metadata list is empty")

    asyncio.run(save_episodes(episodes))

    return dagmatic.StepResult.ok(
        message=f"Loaded {len(episodes)} episodes into the database",
        details={
            "input_path": str(METADATA_PATH),
            "count": len(episodes),
        },
    )
