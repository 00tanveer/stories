"""Pipeline step that loads podcast metadata into Postgres."""

from __future__ import annotations

import asyncio
import json

from tqdm import tqdm

from app.services.podcasts import save_podcast
from app.services.storage import Storage
from app.workers import dagmatic

METADATA_OBJECT = "podcasts_metadata.json"


def build_step() -> dagmatic.Step:
    """Return the dagmatic step used for loading podcasts into the DB."""

    return dagmatic.Step(
        name="step2_load_podcasts",
        description="Step 2b - load podcast metadata into Postgres",
        depends_on=("step1_seed_podcast_list",),
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
        # Show first failure with full error details
        first_error = failures[0]["error"] if failures else "Unknown"
        failure_ids = ", ".join([str(f["podcast_id"]) for f in failures[:3]])
        if len(failures) > 3:
            failure_ids += f" (and {len(failures) - 3} more)"
        return dagmatic.StepResult.failed(
            message=f"Failed to persist {len(failures)} podcasts. First error: {first_error}. Failed IDs: {failure_ids}"
        )

    return dagmatic.StepResult.ok(
        message=f"Loaded {succeeded} podcasts into the database",
        details={
            "metadata_object": METADATA_OBJECT,
            "count": succeeded,
        },
    )


async def _persist_podcasts(podcasts: list[dict[str, object]]) -> tuple[int, list[dict[str, object]]]:
    """Persist podcasts sequentially and collect any failures."""

    succeeded = 0
    failures: list[dict[str, object]] = []
    
    for podcast in tqdm(podcasts, desc="Saving podcasts", unit="podcast"):
        try:
            await save_podcast(podcast)
            succeeded += 1
        except Exception as exc:
            failures.append(
                {
                    "podcast_id": podcast.get("id") or podcast.get("feedId"),
                    "title": podcast.get("title"),
                    "error": repr(exc),
                }
            )

    return succeeded, failures
