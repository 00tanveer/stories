"""Step 1: Upload pod_urls.csv to R2."""

import os
from pathlib import Path
from app.services.storage import Storage
from app.workers import dagmatic

# Dev: /app/data/pod_urls.csv (bind-mounted repo)
# Prod: /opt/stories/pod_urls.csv
LOCAL_PATH = Path("/app/data/pod_urls.csv") if os.getenv("APP_ENV") == "development" else Path("/opt/stories/pod_urls.csv")
R2_KEY = "pod_urls.csv"


def build_step() -> dagmatic.Step:
    return dagmatic.Step(
        name="step1_seed_podcast_list",
        description="Step 1 - upload podcast list to R2",
        depends_on=(),
        run=_run,
    )


def _run(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
    if not LOCAL_PATH.exists():
        return dagmatic.StepResult.failed(f"Missing {LOCAL_PATH}")

    if not Storage().upload_file(str(LOCAL_PATH), R2_KEY):
        return dagmatic.StepResult.failed(f"Failed to upload {R2_KEY} to R2")

    return dagmatic.StepResult.ok(f"Uploaded {R2_KEY} to R2")




