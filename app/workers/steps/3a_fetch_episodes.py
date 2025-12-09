"""Pipeline step that pulls episode metadata for the curated podcasts."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from app.api.podcastindex_api import PDI_API
from app.services.storage import Storage
from app.workers import dagmatic

OUTPUT_PATH = Path("data/podcasts/pod_episodes_metadata.json")
MANIFEST_OBJECT = "pod_urls.csv"
METADATA_OBJECT = "pod_episodes_metadata.json"


def build_step() -> dagmatic.Step:
	"""Return the dagmatic step for fetching episode metadata."""

	return dagmatic.Step(
		name="step3a_fetch_episodes",
		description="Step 3a - fetch episode metadata",
		depends_on=("step2a_fetch_podcasts",),
		run=_run,
	)


def _run(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
	"""Fetch episodes for every feed URL in the seed manifest."""

	try:
		storage = Storage()
	except Exception as exc:  # pragma: no cover - boto errors
		return dagmatic.StepResult.failed(f"Storage client initialisation failed: {exc}")

	manifest_bytes = storage.get_object(MANIFEST_OBJECT)
	if not manifest_bytes:
		return dagmatic.StepResult.failed(
			f"Failed to retrieve podcast manifest '{MANIFEST_OBJECT}' from storage"
		)

	manifest_stream = io.StringIO(manifest_bytes.decode("utf-8"))

	pdi_api = PDI_API()
	episodes: list[dict[str, object]] = []
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
		response = pdi_api.getEpisodesByFeedURL(feed_url)
		if response.get("status_code") == 200 and response.get("success"):
			data = response.get("data") or {}
			items = data.get("items") if isinstance(data, dict) else None
			if items:
				episodes.extend(items)
			else:
				failures.append(
					{
						"feed_url": feed_url,
						"reason": "Empty items payload",
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
				f"Warning: failed to fetch episodes for {feed_url}: {response.get('error') or response}"
			)

	OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
	with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
		json.dump(episodes, handle, indent=2)

	if not storage.upload_file(str(OUTPUT_PATH), METADATA_OBJECT):
		return dagmatic.StepResult.failed(
        f"Failed to upload episode metadata to storage as '{METADATA_OBJECT}'"
		)

	return dagmatic.StepResult.ok(
		message=f"Fetched {len(episodes)} episode records; {len(failures)} failures",
		details={
			"manifest_object": MANIFEST_OBJECT,
			"output_path": str(OUTPUT_PATH),
			"metadata_object": METADATA_OBJECT,
			"count": len(episodes),
			"failures": failures,
		},
	)
