"""Pipeline step that uploads existing transcripts to storage."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.storage import Storage
from app.workers import dagmatic
from tqdm import tqdm

EPISODE_METADATA_OBJECT = "pod_episodes_metadata.json"
TRANSCRIPTS_PREFIX = "transcripts/"
LOCAL_TRANSCRIPTS_DIR = Path("data/transcripts")


def build_step() -> dagmatic.Step:
    """Return the dagmatic step that publishes transcripts to storage."""

    return dagmatic.Step(
        name="step4a_generate_transcripts",
        description="Step 4a - generate transcripts",
        depends_on=("step3b_load_episodes",),
        run=_run,
    )


def _run(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
    """Upload pre-generated transcripts to object storage."""

    try:
        storage = Storage()
    except Exception as exc:  # pragma: no cover - boto errors
        return dagmatic.StepResult.failed(f"Storage client initialisation failed: {exc}")

    episodes_blob = storage.get_object(EPISODE_METADATA_OBJECT)
    if not episodes_blob:
        return dagmatic.StepResult.failed(
            f"Failed to retrieve episode metadata '{EPISODE_METADATA_OBJECT}' from storage"
        )

    try:
        episodes = json.loads(episodes_blob.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return dagmatic.StepResult.failed(f"Invalid episode metadata payload: {exc}")

    if not episodes:
        return dagmatic.StepResult.failed("Episode metadata list is empty")

    # TODO(#assemblyai): integrate AssemblyAI transcription client here so episodes
    # without transcripts are processed automatically using the metadata payload.

    if not LOCAL_TRANSCRIPTS_DIR.exists():
        return dagmatic.StepResult.failed(
            f"Local transcripts directory missing: {LOCAL_TRANSCRIPTS_DIR}"
        )

    uploaded = 0
    skipped = 0
    failures: list[dict[str, object]] = []

    transcript_files = sorted(LOCAL_TRANSCRIPTS_DIR.glob("*.json"))
    for path in tqdm(transcript_files, desc="Uploading transcripts", unit="file"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(
                {
                    "transcript_id": path.stem,
                    "local_path": str(path),
                    "error": f"Invalid JSON: {exc}",
                }
            )
            continue

        transcript_id = str(payload.get("id") or path.stem)
        if not transcript_id:
            failures.append(
                {
                    "transcript_id": path.stem,
                    "local_path": str(path),
                    "error": "Missing transcript id",
                }
            )
            continue

        object_key = f"{TRANSCRIPTS_PREFIX}{transcript_id}.json"
        if storage.object_exists(object_key):
            skipped += 1
            continue
        if not storage.upload_file(str(path), object_key):
            failures.append(
                {
                    "transcript_id": transcript_id,
                    "local_path": str(path),
                    "error": f"Failed to upload transcript to storage ({object_key})",
                }
            )
            continue
        uploaded += 1

    message = (
        f"Uploaded {uploaded} transcripts; {skipped} skipped; {len(failures)} failures"
    )
    return dagmatic.StepResult.ok(
        message=message,
        details={
            "episodes_discovered": len(episodes),
            "uploaded": uploaded,
            "skipped": skipped,
            "failures": failures,
            "storage_prefix": TRANSCRIPTS_PREFIX,
        },
    )