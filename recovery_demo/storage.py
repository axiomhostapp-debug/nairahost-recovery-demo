"""Storage adapters used only for fictional data in this public sample."""

import os
import re
import tempfile
from pathlib import Path
from typing import Protocol


# Keys are opaque generated identifiers, never filesystem paths from users.
_KEY = re.compile(r"[a-f0-9]{32}\.bin\Z")


class BlobStore(Protocol):
    def put(self, key: str, contents: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...


def validate_key(key: str) -> None:
    if not isinstance(key, str) or not _KEY.fullmatch(key):
        raise ValueError("invalid storage key")


class MemoryBlobStore:
    """In-memory adapter for testing; does not talk to cloud storage."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put(self, key: str, contents: bytes) -> None:
        validate_key(key)
        self.objects[key] = bytes(contents)

    def get(self, key: str) -> bytes:
        validate_key(key)
        return self.objects[key]


class LocalBlobStore:
    """Single-user demonstration adapter with atomic file replacement."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, key: str, contents: bytes) -> None:
        validate_key(key)
        temporary_name: str | None = None
        try:
            fd, temporary_name = tempfile.mkstemp(prefix=".upload-", dir=self.root)
            with os.fdopen(fd, "wb") as handle:
                handle.write(contents)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.root / key)
        finally:
            if temporary_name is not None and os.path.exists(temporary_name):
                os.unlink(temporary_name)

    def get(self, key: str) -> bytes:
        validate_key(key)
        return (self.root / key).read_bytes()
