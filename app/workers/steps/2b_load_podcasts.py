"""Pipeline step that loads podcast metadata into Postgres."""

from __future__ import annotations

import asyncio
import json

from app.services.podcasts import save_podcast
from app.services.storage import Storage
from app.workers import dagmatic

METADATA_OBJECT = "podcasts_metadata.json"


def build_step() -> dagmatic.Step:
    """Return the dagmatic step used for loading podcasts into the DB."""

    return dagmatic.Step(
        name="step2b_load_podcasts",
        description="Step 2b - load podcast metadata into Postgres",
        depends_on=("step2a_fetch_podcasts",),
        run=_run,
    )


def _run(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
    """Load podcast metadata rows into the podcasts table."""

    try:
        storage = Storage()
    except Exception as exc:  # pragma: no cover - boto errors
        return dagmatic.StepResult.failed(f"Storage client initialisation failed: {exc}")

    metadata_bytes = storage.get_object(METADATA_OBJECT)
    if not metadata_bytes:
        return dagmatic.StepResult.failed(
            f"Failed to retrieve podcast metadata '{METADATA_OBJECT}' from storage"
        )

    try:
        podcasts = json.loads(metadata_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return dagmatic.StepResult.failed(
            f"Invalid podcast metadata payload from storage: {exc}"
        )

    if not podcasts:
        return dagmatic.StepResult.failed("Podcast metadata list is empty")

    succeeded, failures = asyncio.run(_persist_podcasts(podcasts))

    if failures:
        # Surface the failed podcast IDs without leaking full payloads.
        return dagmatic.StepResult.failed(
            message=f"Failed to persist {len(failures)} podcasts",
            details={
                "metadata_object": METADATA_OBJECT,
                "attempted": len(podcasts),
                "succeeded": succeeded,
                "failures": failures,
            },
        )

    return dagmatic.StepResult.ok(
        message=f"Loaded {succeeded} podcasts into the database",
        details={
            "metadata_object": METADATA_OBJECT,
            "count": succeeded,
        },
    )


async def _persist_podcasts(podcasts: list[dict[str, object]]) -> tuple[int, list[dict[str, object]]]:
    """Persist podcasts concurrently and collect any failures."""

    results = await asyncio.gather(
        *(save_podcast(pod) for pod in podcasts),
        return_exceptions=True,
    )

    succeeded = 0
    failures: list[dict[str, object]] = []
    for podcast, outcome in zip(podcasts, results):
        if isinstance(outcome, Exception):
            failures.append(
                {
                    "podcast_id": podcast.get("id") or podcast.get("feedId"),
                    "title": podcast.get("title"),
                    "error": repr(outcome),
                }
            )
        else:
            succeeded += 1

    return succeeded, failures
