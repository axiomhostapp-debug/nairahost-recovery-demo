import unittest

from recovery_demo.backup_manager import BackupManager, JobError
from recovery_demo.recovery import IntegrityError, RecoveryService
from recovery_demo.storage import MemoryBlobStore


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryBlobStore()
        self.manager = BackupManager(self.store)
        self.service = RecoveryService(self.manager)
        self.job = self.manager.create_job("client-demo")

    def test_owner_may_download_verified_fictional_bytes(self):
        self.manager.run(self.job.id, b"fictional")
        self.assertEqual(self.service.download(self.job.id, "client-demo"), b"fictional")

    def test_other_account_cannot_download(self):
        self.manager.run(self.job.id, b"fictional")
        with self.assertRaises(PermissionError):
            self.service.download(self.job.id, "other-client")

    def test_non_ascii_account_is_denied(self):
        self.manager.run(self.job.id, b"sample")
        with self.assertRaises(PermissionError):
            self.service.download(self.job.id, "caf\u00e9")

    def test_incomplete_job_cannot_download(self):
        with self.assertRaises(JobError):
            self.service.download(self.job.id, "client-demo")

    def test_corrupted_bytes_are_rejected(self):
        self.manager.run(self.job.id, b"original")
        self.store.objects[self.job.object_key] = b"tampered"
        with self.assertRaises(IntegrityError):
            self.service.download(self.job.id, "client-demo")

    def test_unknown_job_has_no_data(self):
        with self.assertRaises(JobError):
            self.service.download("unknown", "client-demo")


if __name__ == "__main__":
    unittest.main()
