# 01_source/payment_gateway/app/core/file_lock.py

from __future__ import annotations

import sys
import time
from typing import BinaryIO

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

_DEFAULT_POLL_INTERVAL_SEC = 0.05


class FileLockTimeout(TimeoutError):
    """Exclusive file lock could not be acquired within the configured timeout."""


class ExclusiveFileLock:
    """
    Cross-platform exclusive advisory lock on an open binary file handle.

    - Linux / macOS: ``fcntl.flock(LOCK_EX)``
    - Windows: ``msvcrt.locking(LK_NBLCK)`` on the first byte

    The lock is always released in :meth:`release` and on context-manager exit,
    including when an exception is raised inside the block.
    """

    def __init__(self, file: BinaryIO, *, timeout_sec: float = 5.0) -> None:
        self._file = file
        self._timeout_sec = timeout_sec
        self._locked = False

    @property
    def locked(self) -> bool:
        return self._locked

    def acquire(self) -> None:
        if self._locked:
            return

        fd = self._file.fileno()
        deadline = time.monotonic() + self._timeout_sec
        while True:
            try:
                _lock_exclusive(fd, self._file)
                self._locked = True
                return
            except (OSError, BlockingIOError):
                if time.monotonic() >= deadline:
                    raise FileLockTimeout(
                        f"exclusive file lock not acquired within {self._timeout_sec}s"
                    ) from None
                time.sleep(_DEFAULT_POLL_INTERVAL_SEC)

    def release(self) -> None:
        if not self._locked:
            return
        try:
            _unlock(self._file.fileno(), self._file)
        except OSError:
            pass
        finally:
            self._locked = False

    def __enter__(self) -> ExclusiveFileLock:
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()


def _lock_exclusive(fd: int, file: BinaryIO) -> None:
    if sys.platform == "win32":
        file.seek(0)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(fd: int, file: BinaryIO) -> None:
    if sys.platform == "win32":
        file.seek(0)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)
