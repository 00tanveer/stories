"""Legacy stub kept for backward compatibility.

The simplified `dagmatic` helper removed explicit input declarations. Import
`Step` / `StepResult` from `app.workers import dagmatic` and handle inputs in
your step code directly.
"""

raise RuntimeError("dagmatic.input has been removed; declare inputs inside your step implementation")
