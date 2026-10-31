"""Simple, in-memory job model for a fictional backup workflow."""

from dataclasses import dataclass
from enum import Enum


class JobState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class BackupJob:
    id: str
    account_id: str
    state: JobState = JobState.PENDING
    attempts: int = 0
    object_key: str | None = None
    sha256: str | None = None
    size_bytes: int = 0
    error_type: str | None = None
