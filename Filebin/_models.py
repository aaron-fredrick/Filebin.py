from __future__ import annotations

import os
from datetime import datetime
from io import BytesIO
from typing import TYPE_CHECKING, List, Optional

from aiohttp import ClientSession
from PIL import Image

from ._constants import BASE_URL
from ._http import parseResponse
from .errors import (
    DownloadCountReached,
    InvalidArchiveType,
    InvalidBin,
    InvalidBinOrFile,
    InvalidFile,
    LockedBin,
    LockFailed,
    StorageFull,
)

if TYPE_CHECKING:
    pass

_DATETIME_FORMATS = ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ")


def _parseDatetime(raw: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 datetime string, trying known formats in order."""
    if raw is None:
        return None
    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


class File:
    """Represents a single file stored inside a Filebin bin."""

    def __init__(self, data: dict, bin: Bin, session: ClientSession) -> None:
        self._session = session
        self._bin = bin
        self._name: Optional[str] = data.get("filename")
        self._content_type: Optional[str] = data.get("content-type")
        self._bytes: Optional[int] = data.get("bytes")
        self._md5: Optional[str] = data.get("md5")
        self._sha256: Optional[str] = data.get("sha256")
        self._updated_at: Optional[datetime] = _parseDatetime(data.get("updated_at"))
        self._created_at: Optional[datetime] = _parseDatetime(data.get("created_at"))
        self._locally_updated_at: datetime = datetime.now()

    @property
    def bin(self) -> Bin:
        return self._bin

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def content_type(self) -> Optional[str]:
        return self._content_type

    @property
    def bytes(self) -> Optional[int]:
        return self._bytes

    @property
    def md5(self) -> Optional[str]:
        return self._md5

    @property
    def sha256(self) -> Optional[str]:
        return self._sha256

    @property
    def updated_at(self) -> Optional[datetime]:
        return self._updated_at

    @property
    def created_at(self) -> Optional[datetime]:
        return self._created_at

    @property
    def locally_updated_at(self) -> datetime:
        return self._locally_updated_at

    async def download(self, path: str = ".") -> bool:
        """
        Download this file to the given local directory.

        The download follows a redirect to S3 storage, streaming the
        response in chunks to avoid loading large files into memory.

        Args:
            path: Local directory path to save the file. Defaults to CWD.

        Returns:
            True if the file was written successfully; False otherwise.

        Raises:
            DownloadCountReached: If the download limit for this file has been hit.
            InvalidFile: If the file no longer exists on the server.
        """
        async with self._session.get(
            f"{self._bin.id}/{self._name}", allow_redirects=False
        ) as redirect_response:
            if redirect_response.status == 403:
                raise DownloadCountReached(self._name)
            if redirect_response.status == 404:
                raise InvalidFile(self._name)

            s3_location = redirect_response.headers.get("Location")
            if redirect_response.status not in (301, 302) or not s3_location:
                return False

        async with ClientSession() as s3_session:
            async with s3_session.get(
                s3_location,
                headers={
                    "Host": "s3.filebin.net",
                    "Referer": "https://filebin.net/",
                    "Accept": "*/*",
                },
                allow_redirects=False,
            ) as s3_response:
                if s3_response.status != 200:
                    return False

                with open(f"{path}/{self._name}", "wb") as f:
                    async for chunk in s3_response.content.iter_any():
                        f.write(chunk)

        return True

    async def delete(self) -> bool:
        """
        Delete this file from its bin.

        Returns:
            True if deletion succeeded.

        Raises:
            InvalidBinOrFile: If the bin or file was not found on the server.
        """
        async with self._session.delete(
            url=f"{BASE_URL}/{self._bin.id}/{self._name}",
            headers={"Accept": "application/json"},
        ) as response:
            if response.status == 200:
                return True
            if response.status == 404:
                raise InvalidBinOrFile(self._bin.id, self._name)

        return False

    def __str__(self) -> str:
        return (
            f"File(\n"
            f"  name         = {self._name}\n"
            f"  bytes        = {self._bytes}\n"
            f"  bin_id       = {self._bin.id}\n"
            f"  sha256       = {self._sha256}\n"
            f"  md5          = {self._md5}\n"
            f")"
        )


class QR:
    """Represents a QR code image for a Filebin bin."""

    def __init__(self, image_bytes: bytes, bin_id: str) -> None:
        self._image_bytes = image_bytes
        self._bin_id = bin_id

    @property
    def image_bytes(self) -> bytes:
        return self._image_bytes

    def show(self) -> None:
        """Display the QR code image using the default image viewer."""
        Image.open(BytesIO(self._image_bytes)).show("bin qr")

    def save(self, path: str = ".") -> None:
        """Save the QR code image as a PNG to the given directory."""
        Image.open(BytesIO(self._image_bytes)).save(f"{path}/{self._bin_id}.png")

    def __str__(self) -> str:
        """Render the QR code as an ANSI block-art string for terminal display."""
        image = Image.open(BytesIO(self._image_bytes)).convert("L")

        console_width = 40
        new_width = int(console_width * 0.8)
        aspect_ratio = image.width / image.height
        new_height = int(new_width / aspect_ratio)
        resized = image.resize((new_width, new_height))

        lines = []
        for y in range(resized.height):
            row = ""
            for x in range(resized.width):
                brightness = resized.getpixel((x, y))
                row += f"\x1b[48;2;{brightness};{brightness};{brightness}m  "
            row += "\x1b[0m"
            lines.append(row)

        return "\n".join(lines)


class Bin:
    """Represents a Filebin bin — a collection of uploaded files."""

    def __init__(self, data: dict, session: ClientSession) -> None:
        self._session = session
        self._qr: Optional[QR] = None
        self._locally_updated_at: datetime = datetime.now()
        self._setProperties(data)

    def _setProperties(self, data: dict) -> None:
        """Populate all bin fields from a raw API response dict."""
        bin_data = data.get("bin", {})
        self._id: Optional[str] = bin_data.get("id")
        self._readonly: Optional[bool] = bin_data.get("readonly")
        self._bytes: Optional[int] = bin_data.get("bytes")

        for key in ("updated_at", "created_at", "expired_at"):
            setattr(self, f"_{key}", _parseDatetime(bin_data.get(key)))

        raw_files = data.get("files") or []
        self._files: List[File] = [
            File(data=f, bin=self, session=self._session) for f in raw_files
        ]

    @property
    def id(self) -> Optional[str]:
        return self._id

    @property
    def readonly(self) -> Optional[bool]:
        return self._readonly

    @property
    def bytes(self) -> Optional[int]:
        return self._bytes

    @property
    def files(self) -> List[File]:
        return self._files

    @property
    def updated_at(self) -> Optional[datetime]:
        return self._updated_at

    @property
    def created_at(self) -> Optional[datetime]:
        return self._created_at

    @property
    def expired_at(self) -> Optional[datetime]:
        return self._expired_at

    @property
    def locally_updated_at(self) -> datetime:
        return self._locally_updated_at

    async def fetchQR(self) -> QR:
        """
        Fetch the QR code image for this bin, caching the result.

        Returns:
            A QR instance wrapping the image bytes.

        Raises:
            InvalidBin: If the bin is not found on the server.
        """
        if self._qr is not None:
            return self._qr

        async with self._session.get(
            f"qr/{self._id}", headers={"Accept": "image/png"}
        ) as response:
            status, body = await parseResponse(response)
            if status == 200:
                self._qr = QR(image_bytes=body, bin_id=self._id)
            elif status == 404:
                raise InvalidBin(self._id)

        return self._qr

    async def update(self) -> Bin:
        """
        Refresh this bin's data from the server.

        Returns:
            Self, for method chaining.
        """
        async with self._session.get(
            url=self._id, headers={"Accept": "application/json"}
        ) as response:
            _, data = await parseResponse(response)
            self._setProperties(data)
            self._locally_updated_at = datetime.now()

        return self

    async def lock(self) -> Bin:
        """
        Lock this bin, making it read-only.

        Returns:
            Self after locking.

        Raises:
            LockFailed: If the server did not confirm the bin is now read-only.
        """
        async with self._session.put(
            url=self._id, headers={"Accept": "application/json"}
        ) as response:
            await parseResponse(response)

        await self.update()

        if not self._readonly:
            raise LockFailed(self._id)

        return self

    async def delete(self) -> bool:
        """
        Delete this entire bin from Filebin.

        Returns:
            True if deletion succeeded.

        Raises:
            InvalidBin: If the bin was not found on the server.
        """
        async with self._session.delete(
            url=self._id, headers={"Accept": "application/json"}
        ) as response:
            if response.status == 200:
                return True
            if response.status == 404:
                raise InvalidBin(self._id)

        return False

    async def downloadArchive(self, archive_type: str, path: str = ".") -> bool:
        """
        Download all files in this bin as a zip or tar archive.

        Args:
            archive_type: Either 'zip' or 'tar'.
            path: Local directory path. Defaults to CWD.

        Returns:
            True if the archive was written successfully.

        Raises:
            InvalidArchiveType: If archive_type is not 'zip' or 'tar'.
            InvalidBin: If the bin was not found on the server.
        """
        if archive_type not in ("zip", "tar"):
            raise InvalidArchiveType(archive_type)

        async with self._session.get(
            url=f"archive/{self._id}/{archive_type}",
            headers={"Accept": "application/json"},
        ) as response:
            if response.status == 200:
                with open(f"{path}/{self._id}.{archive_type}", "wb") as f:
                    async for chunk in response.content.iter_any():
                        f.write(chunk)
                return True
            if response.status == 404:
                raise InvalidBin(self._id)

        return False

    def _findFileByName(self, file_name: str) -> Optional[File]:
        """Return the first file in this bin matching file_name, or None."""
        return next((f for f in self._files if f.name == file_name), None)

    async def getFile(self, file_name: str, from_cache: bool = False) -> File:
        """
        Retrieve a file from this bin by name.

        Args:
            file_name: The filename to look for.
            from_cache: If True, search locally cached files without a network call.

        Returns:
            The matching File instance.

        Raises:
            InvalidFile: If no file with that name exists in this bin.
        """
        if not from_cache:
            await self.update()

        found = self._findFileByName(file_name)
        if found is None:
            raise InvalidFile(file_name)

        return found

    async def downloadFile(self, file_name: str, path: str = ".") -> bool:
        """
        Download a specific file from this bin by name.

        Args:
            file_name: The name of the file to download.
            path: Local directory path. Defaults to CWD.

        Returns:
            True if the file was downloaded successfully.
        """
        file = await self.getFile(file_name)
        return await file.download(path)

    async def deleteFile(self, file_name: str) -> bool:
        """
        Delete a specific file from this bin by name.

        Args:
            file_name: The name of the file to delete.

        Returns:
            True if the file was deleted successfully.
        """
        file = await self.getFile(file_name)
        deleted = await file.delete()
        if deleted:
            self._files.remove(file)
        return deleted

    async def uploadFile(self, file_path: str) -> File:
        """
        Upload a local file to this bin.

        Args:
            file_path: Absolute or relative path to the local file.

        Returns:
            The File instance representing the newly uploaded file.

        Raises:
            InvalidBinOrFile: If the server rejects the upload (400).
            StorageFull: If the bin has no remaining storage (403).
            LockedBin: If the bin is locked and cannot accept uploads (404).
        """
        file_name = os.path.basename(file_path)

        with open(file_path, "rb") as handle:
            async with self._session.post(
                url=f"{self._id}/{file_name}",
                headers={
                    "Accept": "application/json",
                    "cid": "Filebin.py",
                    "Content-Type": "application/octet-stream",
                },
                data=handle,
            ) as response:
                status, data = await parseResponse(response)

        if status == 201:
            new_file = File(data=data.get("file", {}), bin=self, session=self._session)
            self._files.append(new_file)
            return new_file

        if status == 400:
            raise InvalidBinOrFile(bin_id=self._id, file_name=file_name)
        if status == 403:
            raise StorageFull(bin_id=self._id)
        if status == 404:
            raise LockedBin(bin_id=self._id)

        raise RuntimeError(f"Unexpected status {status} while uploading {file_name!r}")

    def __hash__(self) -> int:
        return hash(self._id)

    def __str__(self) -> str:
        return (
            f"Bin(\n"
            f"  id         = {self._id}\n"
            f"  read_only  = {self._readonly}\n"
            f"  bytes      = {self._bytes}\n"
            f"  created_at = {self._created_at}\n"
            f"  updated_at = {self._updated_at}\n"
            f"  expires_at = {self._expired_at}\n"
            f"  files      = {[f.name for f in self._files]}\n"
            f")"
        )
