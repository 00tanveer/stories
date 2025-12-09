"""Pipeline step to build the Elasticsearch utterance index."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from app.services.indexing.elasticsearch_indexer import ESIndexer
from app.workers import dagmatic


def build_step() -> dagmatic.Step:
    """Return the dagmatic step used for Elasticsearch indexing."""

    return dagmatic.Step(
        name="step7_index_elasticsearch",
        description="Step 7 - build Elasticsearch index",
        depends_on=("step4b_load_transcripts",),
        run=_run,
    )


def _run(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
    """Create/update the Elasticsearch utterance index."""

    try:
        summary = asyncio.run(_index_elasticsearch())
    except Exception as exc:  # pragma: no cover - surfaced to CLI
        return dagmatic.StepResult.failed(f"Failed indexing Elasticsearch: {exc}")

    message = (
        f"ES utterances indexed={summary['successes']} (failures={summary['failures']})"
    )

    return dagmatic.StepResult.ok(message=message, details=summary)


async def _index_elasticsearch() -> Dict[str, Any]:
    indexer = ESIndexer()

    # Create/recreate the target index
    indexer.create_index()

    stats = await indexer.insert_utterances()

    return {
        "index": stats.get("index", "utterances"),
        "total": stats.get("total", 0),
        "successes": stats.get("successes", 0),
        "failures": stats.get("failures", 0),
    }