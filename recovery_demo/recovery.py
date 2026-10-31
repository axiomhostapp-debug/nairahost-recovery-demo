"""Read-only retrieval: it returns bytes and never restores an account."""

import hashlib
import hmac

from .backup_manager import BackupManager, JobError
from .models import JobState


class IntegrityError(Exception):
    """Stored content no longer matches the recorded checksum."""


class RecoveryService:
    def __init__(self, manager: BackupManager) -> None:
        self.manager = manager

    def download(self, job_id: str, account_id: str) -> bytes:
        job = self.manager.get_job(job_id)
        if not isinstance(account_id, str) or account_id != job.account_id:
            raise PermissionError("account does not own this job")
        if job.state != JobState.COMPLETE or not job.object_key or not job.sha256:
            raise JobError("job has no completed backup")
        contents = self.manager.store.get(job.object_key)
        if not hmac.compare_digest(hashlib.sha256(contents).hexdigest(), job.sha256):
            raise IntegrityError("checksum verification failed")
        return contents
