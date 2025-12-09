"""Ridiculously small DAG helper for the Stories pipeline."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
from typing import Callable, Iterable, Iterator, Sequence


StepFn = Callable[["StepContext"], "StepResult"]


@dataclass(slots=True)
class Step:
	"""Declarative description of a pipeline step."""

	name: str
	run: StepFn
	depends_on: Sequence[str] = ()
	description: str | None = None


@dataclass(slots=True)
class StepContext:
	"""Execution context handed to each step."""

	run_id: str
	params: dict[str, object]

	def with_params(self, **extra: object) -> dict[str, object]:
		merged = dict(self.params)
		merged.update(extra)
		return merged


@dataclass(slots=True)
class StepResult:
	"""Return value describing the outcome of a step."""

	success: bool
	message: str | None = None
	details: dict[str, object] | None = None

	@staticmethod
	def ok(message: str | None = None, details: dict[str, object] | None = None) -> "StepResult":
		return StepResult(True, message=message, details=details)

	@staticmethod
	def failed(message: str) -> "StepResult":
		return StepResult(False, message=message, details=None)


@dataclass(slots=True)
class DagRunResult:
	"""Aggregate information about a DAG execution."""

	succeeded: list[str]
	skipped: list[str]
	failed: list[tuple[str, str]]


class Dag:
	"""Minimal directed acyclic graph of steps."""

	def __init__(self, steps: Iterable[Step]):
		self._steps = {step.name: step for step in steps}
		self._validate()

	def _validate(self) -> None:
		for step in self._steps.values():
			for dep in step.depends_on:
				if dep not in self._steps:
					raise ValueError(f"Step '{step.name}' depends on unknown step '{dep}'")

	def steps(self, selected: Iterable[str] | None = None) -> Iterator[Step]:
		selected_set = set(selected or self._steps.keys())
		for name in self._topological_order():
			if name in selected_set:
				yield self._steps[name]

	def _topological_order(self) -> list[str]:
		indegree: dict[str, int] = {name: 0 for name in self._steps}
		for step in self._steps.values():
			for dep in step.depends_on:
				indegree[step.name] += 1

		queue = deque([name for name, deg in indegree.items() if deg == 0])
		order: list[str] = []

		while queue:
			name = queue.popleft()
			order.append(name)
			for child in self._steps.values():
				if name in child.depends_on:
					indegree[child.name] -= 1
					if indegree[child.name] == 0:
						queue.append(child.name)

		if len(order) != len(self._steps):
			raise ValueError("Cycle detected in DAG definition")
		return order


_DEFAULT_MANIFEST = Path("data/pipeline_manifest.json")
_PROD_MANIFEST = Path("/opt/stories/pipeline_manifest.json")


def _resolve_manifest_path() -> Path:
	env = os.getenv("APP_ENV", "development").lower()
	return _PROD_MANIFEST if env == "production" else _DEFAULT_MANIFEST


_MANIFEST_PATH = _resolve_manifest_path()


class Executor:
	"""Sequential executor that walks the DAG once."""

	def __init__(self, dag: Dag):
		self._dag = dag

	def run(
		self,
		run_id: str,
		params: dict[str, object] | None = None,
		targets: Iterable[str] | None = None,
		force: bool = False,
	) -> DagRunResult:
		ctx = StepContext(run_id=run_id, params=params or {})
		manifest = _load_manifest()
		manifest_changed = False
		succeeded: list[str] = []
		skipped: list[str] = []
		failed: list[tuple[str, str]] = []

		for step in self._dag.steps(selected=targets):
			if not force and step.name in manifest:
				skipped.append(step.name)
				continue

			try:
				result = step.run(ctx)
			except Exception as exc:  # pragma: no cover - debugging helper
				failed.append((step.name, str(exc)))
				break

			if result.success:
				succeeded.append(step.name)
				manifest[step.name] = _manifest_entry(run_id, result)
				manifest_changed = True
			else:
				failed.append((step.name, result.message or "unknown error"))
				break

		if manifest_changed:
			_save_manifest(manifest)

		return DagRunResult(succeeded=succeeded, skipped=skipped, failed=failed)


def _manifest_entry(run_id: str, result: StepResult) -> dict[str, object]:
	entry: dict[str, object] = {
		"run_id": run_id,
		"updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
	}
	if result.message:
		entry["message"] = result.message
	if result.details:
		entry["details"] = result.details
	return entry


def _load_manifest() -> dict[str, dict[str, object]]:
	if not _MANIFEST_PATH.exists():
		return {}
	try:
		return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
	except json.JSONDecodeError:  # pragma: no cover - corrupt file fallback
		return {}


def _save_manifest(manifest: dict[str, dict[str, object]]) -> None:
	_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
	_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


__all__ = ["Dag", "DagRunResult", "Executor", "Step", "StepContext", "StepResult"]
