"""Unit tests for the errors module — no network required."""

import pytest

from Filebin.errors import (
    DownloadCountReached,
    FilebinError,
    InvalidArchiveType,
    InvalidBin,
    InvalidBinOrFile,
    InvalidFile,
    LockedBin,
    LockFailed,
    StorageFull,
)


def test_all_exceptions_inherit_from_filebin_error():
    exceptions = [
        InvalidArchiveType("xyz"),
        InvalidBin("abc"),
        InvalidFile("file.txt"),
        InvalidBinOrFile("abc", "file.txt"),
        DownloadCountReached("file.txt"),
        StorageFull("abc"),
        LockedBin("abc"),
        LockFailed("abc"),
    ]
    for exc in exceptions:
        assert isinstance(exc, FilebinError)
        assert isinstance(exc, Exception)


def test_invalid_archive_type_message():
    exc = InvalidArchiveType("rar")
    assert "rar" in exc.message
    assert "zip" in exc.message or "tar" in exc.message


def test_invalid_bin_message():
    exc = InvalidBin("my-bin-999")
    assert "my-bin-999" in exc.message


def test_invalid_file_message():
    exc = InvalidFile("secret.txt")
    assert "secret.txt" in exc.message


def test_invalid_bin_or_file_message():
    exc = InvalidBinOrFile("bin-1", "file.txt")
    assert "bin-1" in exc.message
    assert "file.txt" in exc.message


def test_download_count_reached_message():
    exc = DownloadCountReached("report.pdf")
    assert "report.pdf" in exc.message


def test_storage_full_message():
    exc = StorageFull("bin-99")
    assert "bin-99" in exc.message


def test_locked_bin_message():
    exc = LockedBin("bin-locked")
    assert "bin-locked" in exc.message


def test_lock_failed_message():
    exc = LockFailed("bin-xyz")
    assert "bin-xyz" in exc.message


def test_exceptions_are_raiseable():
    with pytest.raises(InvalidBin):
        raise InvalidBin("test")

    with pytest.raises(FilebinError):
        raise InvalidFile("test.txt")
