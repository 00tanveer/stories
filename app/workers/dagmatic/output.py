"""Legacy stub kept for backward compatibility.

Explicit output declarations were removed—steps should manage their own state
and simply return `dagmatic.StepResult` values.
"""

raise RuntimeError("dagmatic.output has been removed; return StepResult.ok/failed instead")