"""
Integration tests for the Filebin API — require network access.

Run with:
    pytest -m network -v

Skip with:
    pytest -m "not network" -v
"""

import os
import tempfile

import pytest
import pytest_asyncio

from Filebin import API
from Filebin.errors import InvalidBin, InvalidFile


# A known public bin on Filebin.net used for read-only integration tests.
# If this bin has been deleted upstream, update to a new public bin ID.
KNOWN_PUBLIC_BIN_ID = "zlpiruayaav16ra2"

pytestmark = pytest.mark.network


@pytest_asyncio.fixture
async def api():
    """Provide a live API session for each test, closed afterwards."""
    async with API() as client:
        yield client


# ---------------------------------------------------------------------------
# Bin tests
# ---------------------------------------------------------------------------


async def test_get_valid_bin_returns_bin_object(api):
    bin = await api.getBin(KNOWN_PUBLIC_BIN_ID)
    assert bin is not None
    assert bin.id == KNOWN_PUBLIC_BIN_ID
    assert isinstance(bin.files, list)


async def test_get_invalid_bin_raises_invalid_bin(api):
    with pytest.raises(InvalidBin):
        await api.getBin("this-bin-does-not-exist-00000000")


async def test_get_bin_from_cache(api):
    bin_live = await api.getBin(KNOWN_PUBLIC_BIN_ID)
    bin_cached = await api.getBin(KNOWN_PUBLIC_BIN_ID, from_cache=True)
    assert bin_live is bin_cached


# ---------------------------------------------------------------------------
# File tests
# ---------------------------------------------------------------------------


async def test_get_file_not_in_bin_raises_invalid_file(api):
    """Requesting a filename that does not exist in a valid bin must raise InvalidFile."""
    with pytest.raises(InvalidFile):
        await api.getFile(KNOWN_PUBLIC_BIN_ID, "this-file-definitely-does-not-exist.xyz")


# ---------------------------------------------------------------------------
# Upload / Delete round-trip
# ---------------------------------------------------------------------------


async def test_upload_and_delete_file(api):
    """Upload a small temp file to a fresh bin, then delete it."""
    import secrets

    fresh_bin_id = f"filebin-py-test-{secrets.token_hex(6)}"
    bin = await api.getBin(fresh_bin_id)

    with tempfile.NamedTemporaryFile(
        suffix=".txt", delete=False, mode="w"
    ) as tmp:
        tmp.write("Filebin.py integration test payload.")
        tmp_path = tmp.name

    try:
        uploaded = await bin.uploadFile(tmp_path)
        assert uploaded is not None
        assert uploaded.name == os.path.basename(tmp_path)

        deleted = await bin.deleteFile(uploaded.name)
        assert deleted is True
    finally:
        os.unlink(tmp_path)
        # Clean up the bin — ignore errors if it fails (e.g. already expired)
        try:
            await api.deleteBin(fresh_bin_id)
        except Exception:
            pass
