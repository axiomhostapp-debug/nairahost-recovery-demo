import tempfile
import unittest

from recovery_demo.storage import LocalBlobStore, MemoryBlobStore

GOOD_KEY = "a" * 32 + ".bin"


class StorageTests(unittest.TestCase):
    def test_memory_round_trip(self):
        store = MemoryBlobStore()
        store.put(GOOD_KEY, b"demo")
        self.assertEqual(store.get(GOOD_KEY), b"demo")

    def test_local_round_trip_and_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LocalBlobStore(directory)
            store.put(GOOD_KEY, b"first")
            store.put(GOOD_KEY, b"second")
            self.assertEqual(store.get(GOOD_KEY), b"second")

    def test_rejects_path_traversal_and_unexpected_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            for store in (LocalBlobStore(directory), MemoryBlobStore()):
                for bad_key in ("../../passwd", "/tmp/x", "..", "abc.bin", GOOD_KEY + "/other"):
                    with self.subTest(key=bad_key), self.assertRaises(ValueError):
                        store.put(bad_key, b"demo")
                    with self.subTest(key=bad_key), self.assertRaises(ValueError):
                        store.get(bad_key)

    def test_missing_object_raises(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LocalBlobStore(directory)
            with self.assertRaises(FileNotFoundError):
                store.get(GOOD_KEY)


if __name__ == "__main__":
    unittest.main()
