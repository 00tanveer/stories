"""Pipeline step that classifies host questions and QA pairs."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Dict, List

from tqdm import tqdm
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.data_models.episode import Episode
from app.db.data_models.transcript import Transcript
from app.db.session import AsyncSessionLocal
from app.language_models.question_detector.src.infer import InferenceModel
from app.workers import dagmatic

MAX_QUESTION_WORDS = 100


def build_step() -> dagmatic.Step:
	"""Return the dagmatic step used for classifying host QA."""

	return dagmatic.Step(
		name="step5_classify_qa",
		description="Step 5 - classify questions & answers",
		depends_on=("step4b_load_transcripts",),
		run=_run,
	)


def _run(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
	"""Detect and persist host questions and QA pairs for each episode."""

	try:
		summary = asyncio.run(_classify_and_save())
	except Exception as exc:  # pragma: no cover - surfaced to CLI
		return dagmatic.StepResult.failed(f"Failed classifying host questions: {exc}")

	episodes = summary["episodes_processed"]
	questions = summary["total_questions"]

	if episodes == 0:
		message = "No episodes with transcripts available for classification"
	else:
		message = f"Processed {episodes} episodes; detected {questions} host questions"

	return dagmatic.StepResult.ok(message=message, details=summary)


async def _classify_and_save() -> Dict[str, Any]:
	model = InferenceModel()

	episodes = await _fetch_episodes_with_transcripts()
	if not episodes:
		return {
			"episodes_processed": 0,
			"episodes_with_questions": 0,
			"total_questions": 0,
			"total_question_answers": 0,
			"model_path": str(model.model_dir),
		}

	results: List[Dict[str, Any]] = []
	total_questions_so_far = 0

	with tqdm(episodes, desc="Classifying questions", unit="episode") as progress:
		for episode in progress:
			result = _classify_episode(episode, model)
			results.append(result)

			question_count = len(result["host_questions"])
			qa_count = len(result["question_answers"])
			total_questions_so_far += question_count
			progress.set_postfix({
				"episode": episode.id,
				"questions": question_count,
				"total": total_questions_so_far,
			})
			print(
				f"[step5_classify_qa] episode {episode.id}: "
				f"{question_count} host questions, {qa_count} QA pairs; "
				f"running total {total_questions_so_far}"
			)
	episodes_with_questions = sum(1 for item in results if item["host_questions"])
	total_questions = sum(len(item["host_questions"]) for item in results)
	total_question_answers = sum(len(item["question_answers"]) for item in results)

	await _persist_classifications(results)

	return {
		"episodes_processed": len(results),
		"episodes_with_questions": episodes_with_questions,
		"total_questions": total_questions,
		"total_question_answers": total_question_answers,
		"model_path": str(model.model_dir),
	}


async def _fetch_episodes_with_transcripts() -> List[Episode]:
	async with AsyncSessionLocal() as session:
		stmt = (
			select(Episode)
			.join(Episode.transcript)
			.options(selectinload(Episode.transcript).selectinload(Transcript.utterances))
		)
		result = await session.execute(stmt)
		episodes = result.scalars().all()

	# Ensure deterministic ordering (use id to keep manifest diff stable)
	return sorted(episodes, key=lambda ep: ep.id)


def _classify_episode(episode: Episode, model: InferenceModel) -> Dict[str, Any]:
	transcript = episode.transcript
	if transcript is None or not transcript.utterances:
		return {
			"episode_id": episode.id,
			"host_questions": [],
			"question_answers": [],
		}

	utterances = sorted(transcript.utterances, key=lambda utt: (utt.start, utt.end))
	guest = _detect_guest(utterances)

	host_questions: List[Dict[str, Any]] = []
	question_answers: List[Dict[str, str]] = []

	for idx, utterance in enumerate(utterances[:-1]):
		if guest is not None and utterance.speaker == guest:
			continue
		if not _looks_like_question(utterance.text, model):
			continue

		host_questions.append(
			{
				"start": int(utterance.start),
				"end": int(utterance.end),
				"confidence": float(utterance.confidence),
				"speaker": utterance.speaker,
				"text": utterance.text,
			}
		)

		answer_utterance = utterances[idx + 1]
		question_answers.append({"question": utterance.text, "answer": answer_utterance.text})

	return {
		"episode_id": episode.id,
		"host_questions": host_questions,
		"question_answers": question_answers,
	}


def _looks_like_question(text: str, model: InferenceModel) -> bool:
	if not text:
		return False
	if len(text.split()) > MAX_QUESTION_WORDS:
		return False
	try:
		prediction = model.predict(text)
	except Exception:
		return False
	if not prediction:
		return False
	top = prediction[0]
	return top.get("label") == "LABEL_1"


def _detect_guest(utterances: List[Any]) -> str | None:
	if not utterances:
		return None

	word_counts: Dict[str, int] = defaultdict(int)
	for utt in utterances:
		speaker = utt.speaker or ""
		word_counts[speaker] += len(utt.text.split()) if utt.text else 0

	if not word_counts:
		return None

	return max(word_counts, key=word_counts.get)


async def _persist_classifications(results: List[Dict[str, Any]]) -> None:
	if not results:
		return

	async with AsyncSessionLocal() as session:
		async with session.begin():
			for item in results:
				episode = await session.get(Episode, item["episode_id"])
				if episode is None:
					continue
				episode.host_questions = item["host_questions"]
				episode.question_answers = item["question_answers"]

