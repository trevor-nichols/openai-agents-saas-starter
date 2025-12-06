"""Home hub workflows.

Provides the interactive/summary home hub that surfaces probe results and
quick actions. Uses the same probe engine as the doctor command.
"""

from .service import HomeController, HomeSummary

__all__ = ["HomeController", "HomeSummary"]
