"""Legacy stub kept for backward compatibility.

The simplified `dagmatic` surface no longer exposes artifact helpers. Import
`Step` / `Executor` / `StepResult` directly from `app.workers import dagmatic`.
"""

raise RuntimeError("dagmatic.artifacts has been removed; use the simplified dagmatic API instead")
