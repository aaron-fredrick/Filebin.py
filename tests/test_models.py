"""
Unit tests for Bin and File model classes.

All tests use fixture data — no network calls required.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from Filebin._models import Bin


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BIN_ID = "test-bin-id"

RAW_BIN_RESPONSE = {
    "bin": {
        "id": BIN_ID,
        "readonly": False,
        "bytes": 2048,
        "created_at": "2024-01-15T10:30:00.000Z",
        "updated_at": "2024-01-15T11:00:00.500Z",
        "expired_at": "2024-02-15T10:30:00.000Z",
    },
    "files": [
        {
            "filename": "hello.txt",
            "content-type": "text/plain",
            "bytes": 512,
            "md5": "abc123",
            "sha256": "def456",
            "created_at": "2024-01-15T10:31:00.000Z",
            "updated_at": "2024-01-15T10:31:00.000Z",
        }
    ],
}

RAW_BIN_NO_FILES = {
    "bin": {
        "id": "empty-bin",
        "readonly": True,
        "bytes": 0,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "expired_at": None,
    },
}


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def bin_with_files(mock_session):
    return Bin(data=RAW_BIN_RESPONSE, session=mock_session)


@pytest.fixture
def empty_bin(mock_session):
    return Bin(data=RAW_BIN_NO_FILES, session=mock_session)


# ---------------------------------------------------------------------------
# Bin property tests
# ---------------------------------------------------------------------------


def test_bin_id(bin_with_files):
    assert bin_with_files.id == BIN_ID


def test_bin_readonly_false(bin_with_files):
    assert bin_with_files.readonly is False


def test_bin_readonly_true(empty_bin):
    assert empty_bin.readonly is True


def test_bin_bytes(bin_with_files):
    assert bin_with_files.bytes == 2048


def test_bin_created_at_is_datetime(bin_with_files):
    assert isinstance(bin_with_files.created_at, datetime)


def test_bin_updated_at_is_datetime(bin_with_files):
    assert isinstance(bin_with_files.updated_at, datetime)


def test_bin_expired_at_is_datetime(bin_with_files):
    assert isinstance(bin_with_files.expired_at, datetime)


def test_bin_expired_at_none_when_missing(empty_bin):
    assert empty_bin.expired_at is None


def test_bin_locally_updated_at_is_datetime(bin_with_files):
    assert isinstance(bin_with_files.locally_updated_at, datetime)


def test_bin_files_is_list(bin_with_files):
    assert isinstance(bin_with_files.files, list)


def test_bin_files_populated(bin_with_files):
    assert len(bin_with_files.files) == 1


def test_bin_empty_files_when_no_key(empty_bin):
    assert empty_bin.files == []


def test_bin_str_contains_id(bin_with_files):
    result = str(bin_with_files)
    assert BIN_ID in result


# ---------------------------------------------------------------------------
# File property tests
# ---------------------------------------------------------------------------


@pytest.fixture
def file_instance(bin_with_files):
    return bin_with_files.files[0]


def test_file_name(file_instance):
    assert file_instance.name == "hello.txt"


def test_file_content_type(file_instance):
    assert file_instance.content_type == "text/plain"


def test_file_bytes(file_instance):
    assert file_instance.bytes == 512


def test_file_md5(file_instance):
    assert file_instance.md5 == "abc123"


def test_file_sha256(file_instance):
    assert file_instance.sha256 == "def456"


def test_file_created_at_is_datetime(file_instance):
    assert isinstance(file_instance.created_at, datetime)


def test_file_updated_at_is_datetime(file_instance):
    assert isinstance(file_instance.updated_at, datetime)


def test_file_locally_updated_at_is_datetime(file_instance):
    assert isinstance(file_instance.locally_updated_at, datetime)


def test_file_bin_reference(file_instance, bin_with_files):
    assert file_instance.bin is bin_with_files


def test_file_str_contains_name(file_instance):
    result = str(file_instance)
    assert "hello.txt" in result


# ---------------------------------------------------------------------------
# Datetime parsing edge cases
# ---------------------------------------------------------------------------


def test_bin_accepts_datetime_without_microseconds(mock_session):
    data = {
        "bin": {
            "id": "dt-test",
            "created_at": "2024-06-01T12:00:00Z",
            "updated_at": "2024-06-01T12:00:00Z",
            "expired_at": None,
        }
    }
    b = Bin(data=data, session=mock_session)
    assert isinstance(b.created_at, datetime)


def test_bin_tolerates_missing_optional_fields(mock_session):
    data = {"bin": {"id": "minimal-bin"}}
    b = Bin(data=data, session=mock_session)
    assert b.id == "minimal-bin"
    assert b.readonly is None
    assert b.bytes is None
    assert b.created_at is None
    assert b.files == []


# ---------------------------------------------------------------------------
# _findFileByName
# ---------------------------------------------------------------------------


def test_find_file_by_name_returns_correct_file(bin_with_files):
    result = bin_with_files._findFileByName("hello.txt")
    assert result is not None
    assert result.name == "hello.txt"


def test_find_file_by_name_returns_none_for_missing(bin_with_files):
    result = bin_with_files._findFileByName("nonexistent.txt")
    assert result is None
