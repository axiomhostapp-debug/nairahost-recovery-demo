"""Small backup-job state machine, deliberately independent of real servers."""

import hashlib
import re
import uuid

from .models import BackupJob, JobState
from .storage import BlobStore

_ACCOUNT = re.compile(r"[a-z][a-z0-9_-]{1,31}\Z")


class JobError(Exception):
    """A job cannot be created or run in its current state."""


class BackupManager:
    def __init__(self, store: BlobStore, max_attempts: int = 3) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        self.store = store
        self.max_attempts = max_attempts
        self.jobs: dict[str, BackupJob] = {}

    def create_job(self, account_id: str) -> BackupJob:
        if not isinstance(account_id, str) or not _ACCOUNT.fullmatch(account_id):
            raise ValueError("account_id must be 2-32 lowercase safe characters")
        job = BackupJob(id=uuid.uuid4().hex, account_id=account_id)
        self.jobs[job.id] = job
        return job

    def get_job(self, job_id: str) -> BackupJob:
        try:
            return self.jobs[job_id]
        except KeyError as exc:
            raise JobError("unknown job") from exc

    def run(self, job_id: str, payload: bytes) -> BackupJob:
        """Store supplied bytes; never reads any real user or server data."""
        job = self.get_job(job_id)
        if job.state == JobState.COMPLETE:
            return job  # Re-running a completed job does not upload again.
        if job.state == JobState.RUNNING:
            raise JobError("job already running")
        if job.attempts >= self.max_attempts:
            raise JobError("attempt limit reached")
        if not isinstance(payload, bytes) or not payload:
            raise ValueError("nonempty bytes payload required")

        job.state = JobState.RUNNING
        job.attempts += 1
        object_key = f"{job.id}.bin"
        try:
            self.store.put(object_key, payload)
        except Exception as exc:
            job.state = JobState.FAILED
            job.error_type = type(exc).__name__  # Do not leak exception details.
            raise JobError("storage operation failed") from exc

        job.object_key = object_key
        job.sha256 = hashlib.sha256(payload).hexdigest()
        job.size_bytes = len(payload)
        job.error_type = None
        job.state = JobState.COMPLETE
        return job
