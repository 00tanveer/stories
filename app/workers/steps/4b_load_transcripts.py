"""Pipeline step that loads generated transcripts into Postgres."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from app.services.podcasts import save_transcripts
from app.workers import dagmatic

DEFAULT_TRANSCRIPTS_DIR = Path("data/transcripts")
PROD_TRANSCRIPTS_DIR = Path("/opt/stories/transcripts")


def _resolve_transcripts_dir() -> Path:
    env = os.getenv("APP_ENV", "development").lower()
    return PROD_TRANSCRIPTS_DIR if env == "production" else DEFAULT_TRANSCRIPTS_DIR


TRANSCRIPTS_DIR = _resolve_transcripts_dir()


def build_step() -> dagmatic.Step:
    """Return the dagmatic step used for loading transcript data."""

    return dagmatic.Step(
        name="step4b_load_transcripts",
        description="Step 4b - load transcript tables",
        depends_on=(),
        run=_run,
    )


def _run(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
    """Persist transcript JSON files and their child objects."""

    if not TRANSCRIPTS_DIR.exists() or not TRANSCRIPTS_DIR.is_dir():
        return dagmatic.StepResult.failed(f"Transcript directory not found: {TRANSCRIPTS_DIR}")

    transcripts: list[dict[str, object]] = []
    for path in sorted(TRANSCRIPTS_DIR.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                transcripts.append(json.load(handle))
        except json.JSONDecodeError as exc:
            return dagmatic.StepResult.failed(f"Invalid transcript JSON at {path}: {exc}")

    if not transcripts:
        return dagmatic.StepResult.failed(f"No transcript json files found in {TRANSCRIPTS_DIR}")

    asyncio.run(save_transcripts(transcripts))

    return dagmatic.StepResult.ok(
        message=f"Loaded {len(transcripts)} transcripts into the database",
        details={
            "directory": str(TRANSCRIPTS_DIR),
            "count": len(transcripts),
        },
    )
