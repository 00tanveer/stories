"""Pipeline step that loads episode metadata into Postgres."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.services.podcasts import save_episodes
from app.services.storage import Storage
from app.workers import dagmatic

METADATA_OBJECT = "pod_episodes_metadata.json"


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

    try:
        storage = Storage()
    except Exception as exc:  # pragma: no cover - boto errors
        return dagmatic.StepResult.failed(f"Storage client initialisation failed: {exc}")

    metadata_bytes = storage.get_object(METADATA_OBJECT)
    if not metadata_bytes:
        return dagmatic.StepResult.failed(
            f"Failed to retrieve episode metadata '{METADATA_OBJECT}' from storage"
        )

    try:
        episodes = json.loads(metadata_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return dagmatic.StepResult.failed(
            f"Invalid episode metadata payload from storage: {exc}"
        )

    if not episodes:
        return dagmatic.StepResult.failed("Episode metadata list is empty")

    asyncio.run(save_episodes(episodes))

    return dagmatic.StepResult.ok(
        message=f"Loaded {len(episodes)} episodes into the database",
        details={
            "metadata_object": METADATA_OBJECT,
            "count": len(episodes),
        },
    )
