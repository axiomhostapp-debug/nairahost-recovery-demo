# NairaHost Recovery Demo

A standalone Python demo of backup job tracking, retries, and verified downloads. It uses sample data and local storage. The production NairaHost Recovery Manager is private and is not included here.

## Run

Python 3.10 or newer is required. No dependencies or credentials are needed.

```bash
python -m recovery_demo.cli
python -m unittest discover -s tests -v
```

## How it works

`BackupManager` creates jobs and writes supplied bytes through a storage adapter. A successful write records the object key, size, and SHA-256 checksum. Failed writes can be retried up to the configured attempt limit; running a completed job again leaves its stored data unchanged.

`RecoveryService` checks the supplied account ID against the job owner and verifies the checksum before returning the stored bytes. `MemoryBlobStore` supports tests, while `LocalBlobStore` writes files using atomic replacement.

## Files

- `backup_manager.py`: job lifecycle and retry limits
- `models.py`: job states and metadata
- `storage.py`: storage interface and adapters
- `recovery.py`: ownership and integrity checks
- `cli.py`: an end-to-end example
- `tests/`: success paths, failed writes, retry limits, invalid keys, account checks, and corrupted data

## Scope

Jobs are kept in memory and execution is single-threaded. The account ID is supplied by the caller; this demo does not implement authentication. The local storage directory must be trusted and controlled by the process owner. Downloads return bytes without extracting archives or restoring accounts.

There are no cPanel, WHMCS, or cloud storage integrations, production credentials, or customer records in this repository.

## License

Provided for code review. No open-source license is granted.
