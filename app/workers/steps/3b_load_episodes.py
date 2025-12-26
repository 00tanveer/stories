"""Pipeline step that loads episode metadata into Postgres."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from tqdm import tqdm

from app.services.podcasts import save_episodes
from app.services.storage import Storage
from app.workers import dagmatic

METADATA_OBJECT = "pod_episodes_metadata.json"


def build_step() -> dagmatic.Step:
    """Return the dagmatic step used for loading episode metadata."""

    return dagmatic.Step(
        name="step3b_load_episodes",
        description="Step 3b - load episode metadata into Postgres",
        depends_on=("step2_load_podcasts",),
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

    succeeded, failures = asyncio.run(save_episodes(episodes))

    if failures:
        # Surface the failed episode IDs without leaking full payloads.
        # Show first failure with full error details
        first_error = failures[0]["error"] if failures else "Unknown"
        failure_ids = ", ".join([str(f["episode_id"]) for f in failures[:3]])
        if len(failures) > 3:
            failure_ids += f" (and {len(failures) - 3} more)"
        return dagmatic.StepResult.failed(
            message=f"Failed to persist {len(failures)} episodes. First error: {first_error}. Failed IDs: {failure_ids}"
        )

    return dagmatic.StepResult.ok(
        message=f"Loaded {succeeded} episodes into the database",
        details={
            "metadata_object": METADATA_OBJECT,
            "count": succeeded,
        },
    )
