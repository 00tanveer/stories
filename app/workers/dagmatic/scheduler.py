"""Legacy stub kept for backward compatibility.

Scheduler logic now lives directly in `dagmatic.__init__`. Import `Dag` and
`Executor` from there instead of this module.
"""

raise RuntimeError("dagmatic.scheduler has been removed; import Dag/Executor from dagmatic instead")
