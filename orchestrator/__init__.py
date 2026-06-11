"""AI-оркестратор: координация нескольких LLM через общее файловое пространство."""
from .orchestrator import Orchestrator, RunReport, Step, StepRecord
from .protocol import Action, AgentResult, FileChange, Status
from .workspace import Workspace

__version__ = "0.1.0"

__all__ = [
    "Orchestrator", "Step", "StepRecord", "RunReport",
    "Workspace", "AgentResult", "FileChange", "Action", "Status",
]
