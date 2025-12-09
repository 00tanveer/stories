"""Bootstrap definition for pipeline step 1 (seed podcast list)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from app.services.storage import Storage
from app.workers import dagmatic

_DEFAULT_MANIFEST_PATH = Path("/opt/stories/pod_urls.csv")
_MANIFEST_ENV = "PODCAST_MANIFEST_PATH"
_MANIFEST_OBJECT_ENV = "PODCAST_MANIFEST_OBJECT"
_DEFAULT_OBJECT_KEY = "pod_urls.csv"


def build_step() -> dagmatic.Step:
    """Return the dagmatic.Step used by the pipeline runner."""

    return dagmatic.Step(
        name="step1_seed_podcast_list",
        description="Step 1 - curate podcast list",
        depends_on=(),
        run=_run,
    )


def _run(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
    """Seed the podcast list by uploading the manifest to object storage."""

    manifest_path = _resolve_manifest_path()
    if not manifest_path.exists() or not manifest_path.is_file():
        return dagmatic.StepResult.failed(f"Missing podcast manifest at {manifest_path}")

    try:
        file_size = manifest_path.stat().st_size
    except OSError as exc:
        return dagmatic.StepResult.failed(f"Unable to read manifest metadata: {exc}")

    if file_size == 0:
        return dagmatic.StepResult.failed(f"Podcast manifest is empty: {manifest_path}")

    checksum = _file_checksum(manifest_path)
    object_key = os.getenv(_MANIFEST_OBJECT_ENV, _DEFAULT_OBJECT_KEY)

    try:
        storage = Storage()
    except Exception as exc:  # pragma: no cover - boto can raise many errors
        return dagmatic.StepResult.failed(f"Storage client initialisation failed: {exc}")

    if not storage.upload_file(str(manifest_path), object_key):
        return dagmatic.StepResult.failed(
            f"Failed to upload podcast manifest to object storage as {object_key}"
        )

    return dagmatic.StepResult.ok(
        message=f"Uploaded podcast manifest to object storage ({object_key})",
        details={
            "manifest_path": str(manifest_path),
            "object_key": object_key,
            "size_bytes": file_size,
            "md5": checksum,
        },
    )


def _resolve_manifest_path() -> Path:
    raw_path = os.getenv(_MANIFEST_ENV)
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    return _DEFAULT_MANIFEST_PATH


def _file_checksum(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()




