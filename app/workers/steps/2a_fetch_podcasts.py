"""Pipeline step that fetches podcast metadata from PodcastIndex."""

from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path

from app.api.podcastindex_api import PDI_API
from app.services.storage import Storage
from app.workers import dagmatic

DEFAULT_OUTPUT_PATH = Path("data/podcasts/podcasts_metadata.json")
PROD_OUTPUT_PATH = Path("/opt/stories/podcasts_metadata.json")

MANIFEST_OBJECT = "pod_urls.csv"
METADATA_OBJECT = "podcasts_metadata.json"


def _resolve_output_path() -> Path:
    env = os.getenv("APP_ENV", "development").lower()
    return PROD_OUTPUT_PATH if env == "production" else DEFAULT_OUTPUT_PATH


OUTPUT_PATH = _resolve_output_path()


def build_step() -> dagmatic.Step:
    """Return a dagmatic step definition for fetching podcast metadata."""

    return dagmatic.Step(
        name="step2a_fetch_podcasts",
        description="Step 2a - fetch podcast metadata",
        depends_on=("step1_seed_podcast_list",),
        run=_run,
    )


def _run(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
    """Fetch metadata for each seed feed URL and write it to disk."""

    try:
        storage = Storage()
    except Exception as exc:  # pragma: no cover - boto can raise many errors
        return dagmatic.StepResult.failed(f"Storage client initialisation failed: {exc}")

    manifest_bytes = storage.get_object(MANIFEST_OBJECT)
    if not manifest_bytes:
        return dagmatic.StepResult.failed(
            f"Failed to retrieve podcast manifest '{MANIFEST_OBJECT}' from storage"
        )

    manifest_stream = io.StringIO(manifest_bytes.decode("utf-8"))

    pdi_api = PDI_API()
    pods: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []

    reader = csv.reader(manifest_stream)
    try:
        next(reader)
    except StopIteration:
        return dagmatic.StepResult.failed("Seed feed list is empty")

    for row in reader:
        if not row:
            continue
        raw_feed = row[2] if len(row) > 2 else ""
        feed_url = raw_feed.strip().strip('"').strip("'").rstrip(",")
        if not feed_url:
            continue
        response = pdi_api.getPodcastByFeedURL(feed_url)
        if response.get("status_code") == 200 and response.get("success"):
            data = response.get("data") or {}
            feed = data.get("feed") if isinstance(data, dict) else None
            if feed:
                pods.append(feed)
            else:
                failures.append(
                    {
                        "feed_url": feed_url,
                        "reason": "Empty feed payload",
                    }
                )
        else:
            failures.append(
                {
                    "feed_url": feed_url,
                    "status_code": response.get("status_code"),
                    "error": response.get("error") or response,
                }
            )
            print(
                f"Warning: failed to fetch {feed_url}: {response.get('error') or response}"
            )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(pods, handle, indent=2)

    if not storage.upload_file(str(OUTPUT_PATH), METADATA_OBJECT):
        return dagmatic.StepResult.failed(
            f"Failed to upload podcast metadata to storage as '{METADATA_OBJECT}'"
        )

    return dagmatic.StepResult.ok(
        message=f"Fetched {len(pods)} podcast records; {len(failures)} failures",
        details={
            "manifest_object": MANIFEST_OBJECT,
            "output_path": str(OUTPUT_PATH),
            "metadata_object": METADATA_OBJECT,
            "count": len(pods),
            "failures": failures,
        },
    )
