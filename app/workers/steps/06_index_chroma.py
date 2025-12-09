"""Pipeline step that builds Chroma collections."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from app.services.indexing.chroma_indexer import ChromaIndexer
from app.workers import dagmatic


def build_step() -> dagmatic.Step:
	"""Return the dagmatic step used for Chroma indexing."""

	return dagmatic.Step(
		name="step6_index_chroma",
		description="Step 6 - index Chroma collections",
		depends_on=("step5_classify_qa",),
		run=_run,
	)


def _run(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
	"""Create/update Chroma collections for QA pairs and utterances."""

	try:
		summary = asyncio.run(_index_collections())
	except Exception as exc:  # pragma: no cover - surfaced to CLI
		return dagmatic.StepResult.failed(f"Failed indexing Chroma collections: {exc}")

	message = (
		f"Chroma QA docs={summary['qa_count']} (Δ {summary['qa_delta']}) | "
		f"Utterances={summary['utterance_count']} (Δ {summary['utterance_delta']})"
	)

	return dagmatic.StepResult.ok(message=message, details=summary)


async def _index_collections() -> Dict[str, Any]:
	indexer = ChromaIndexer()

	qa_before = _collection_count(indexer, indexer.qa_collection_name)
	await indexer.upsert_qa_collection()
	qa_after = _collection_count(indexer, indexer.qa_collection_name)

	utter_before = _collection_count(indexer, indexer.utterances_collection_name)
	await indexer.upsert_utterances_collection()
	utter_after = _collection_count(indexer, indexer.utterances_collection_name)

	return {
		"qa_collection": indexer.qa_collection_name,
		"qa_count": qa_after,
		"qa_delta": qa_after - qa_before,
		"utterance_collection": indexer.utterances_collection_name,
		"utterance_count": utter_after,
		"utterance_delta": utter_after - utter_before,
	}


def _collection_count(indexer: ChromaIndexer, collection_name: str) -> int:
	if not collection_name:
		return 0

	try:
		collection = indexer.chroma_client.get_collection(collection_name)
	except Exception:  # pragma: no cover - chroma raises custom errors
		return 0

	try:
		return int(collection.count())
	except Exception:  # pragma: no cover - defensive guard
		return 0