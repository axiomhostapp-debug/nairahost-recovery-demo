import unittest

from recovery_demo.backup_manager import BackupManager, JobError
from recovery_demo.models import JobState
from recovery_demo.storage import MemoryBlobStore


class CountingStore(MemoryBlobStore):
    def __init__(self):
        super().__init__()
        self.writes = 0

    def put(self, key, contents):
        self.writes += 1
        super().put(key, contents)


class FailingOnceStore(MemoryBlobStore):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def put(self, key, contents):
        self.calls += 1
        if self.calls == 1:
            raise OSError("illustrative transient problem")
        super().put(key, contents)


class BackupManagerTests(unittest.TestCase):
    def test_happy_path_and_metadata(self):
        manager = BackupManager(MemoryBlobStore())
        job = manager.create_job("demo-account")
        manager.run(job.id, b"test data")
        self.assertEqual(job.state, JobState.COMPLETE)
        self.assertEqual(job.size_bytes, 9)
        self.assertEqual(len(job.sha256), 64)

    def test_invalid_account_rejected(self):
        manager = BackupManager(MemoryBlobStore())
        for value in ("../secret", "UPPERCASE", "a", "", "bad/name"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                manager.create_job(value)

    def test_empty_payload_rejected_without_state_change(self):
        manager = BackupManager(MemoryBlobStore())
        job = manager.create_job("demo-user")
        with self.assertRaises(ValueError):
            manager.run(job.id, b"")
        self.assertEqual(job.state, JobState.PENDING)
        self.assertEqual(job.attempts, 0)

    def test_completed_job_is_idempotent(self):
        store = CountingStore()
        manager = BackupManager(store)
        job = manager.create_job("demo-user")
        manager.run(job.id, b"one")
        manager.run(job.id, b"two")
        self.assertEqual(store.writes, 1)
        self.assertEqual(store.get(job.object_key), b"one")

    def test_failure_then_retry(self):
        store = FailingOnceStore()
        manager = BackupManager(store)
        job = manager.create_job("demo-user")
        with self.assertRaises(JobError):
            manager.run(job.id, b"safe")
        self.assertEqual(job.state, JobState.FAILED)
        self.assertEqual(job.error_type, "OSError")
        manager.run(job.id, b"safe")
        self.assertEqual(job.state, JobState.COMPLETE)
        self.assertEqual(job.attempts, 2)
        self.assertIsNone(job.error_type)

    def test_failed_job_stops_after_attempt_limit(self):
        class AlwaysFail(MemoryBlobStore):
            def put(self, key, contents):
                raise OSError("temporary")

        manager = BackupManager(AlwaysFail(), max_attempts=2)
        job = manager.create_job("demo-user")
        for _ in range(2):
            with self.assertRaises(JobError):
                manager.run(job.id, b"sample")
        with self.assertRaisesRegex(JobError, "attempt limit"):
            manager.run(job.id, b"sample")
        self.assertEqual(job.attempts, 2)

    def test_missing_job(self):
        manager = BackupManager(MemoryBlobStore())
        with self.assertRaisesRegex(JobError, "unknown job"):
            manager.get_job("no-such-job")

    def test_zero_max_attempts_rejected(self):
        with self.assertRaises(ValueError):
            BackupManager(MemoryBlobStore(), max_attempts=0)


if __name__ == "__main__":
    unittest.main()
