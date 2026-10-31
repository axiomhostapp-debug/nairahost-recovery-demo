"""Run a completely fictional backup and download example."""

import hashlib

from .backup_manager import BackupManager
from .recovery import RecoveryService
from .storage import MemoryBlobStore


def main() -> None:
    manager = BackupManager(store=MemoryBlobStore())
    job = manager.create_job("example-account")
    sample_data = b"Illustrative test bytes; no customer data or real backup."
    manager.run(job.id, sample_data)
    downloaded = RecoveryService(manager).download(job.id, "example-account")
    assert downloaded == sample_data
    print(f"Demo job state: {job.state.value}")
    print(f"Demo data verified: {job.sha256 == hashlib.sha256(downloaded).hexdigest()}")
    print("No real account was backed up or restored.")


if __name__ == "__main__":
    main()
