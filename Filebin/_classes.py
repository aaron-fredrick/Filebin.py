from __future__ import annotations
import os

import aiohttp
from aiohttp import ClientSession
from datetime import datetime
from .Errors import *
from io import BytesIO
import numpy as np
from PIL import Image
from typing import TYPE_CHECKING, Tuple, Union, Optional, List, Any, Self

from ._constants import BASE_URL
from ._utils import _fetch, _response_parser


class _FILE:
    def __init__(FILE, _f: dict, _bin: _BIN, _s: ClientSession) -> _FILE:
        # BIN info
        FILE.__session = _s
        FILE.__bin = _bin

        # file properties
        FILE.__name = _f.get("filename", None)
        FILE.__content_type = _f.get("content-type", None)
        FILE.__bytes = _f.get("bytes", None)
        FILE.__md5 = _f.get("md5", None)
        FILE.__sha256 = _f.get("sha256", None)
        FILE.__updated_at = datetime.strptime(
            _dt, "%Y-%m-%dT%H:%M:%S.%fZ") if (_dt := _f.get("updated_at", None)) is not None else None
        FILE.__created_at = datetime.strptime(
            _dt, "%Y-%m-%dT%H:%M:%S.%fZ") if (_dt := _f.get("created_at", None)) is not None else None

        FILE.__locally_updated_at = datetime.now()

    # properties
    @property
    def bin(FILE) -> _BIN:
        return FILE.__bin

    @property
    def name(FILE) -> Optional[str]:
        return FILE.__name

    @property
    def content_type(FILE) -> bool | None:
        return FILE.__content_type

    @property
    def bytes(FILE) -> int | None:
        return FILE.__bytes

    @property
    def md5(FILE) -> int | None:
        return FILE.__md5

    @property
    def sha256(FILE) -> int | None:
        return FILE.__sha256

    @property
    def updated_at(FILE) -> Optional[datetime]:
        return FILE.__updated_at

    @property
    def created_at(FILE) -> Optional[datetime]:
        return FILE.__created_at

    @property
    def locally_updated_at(FILE) -> datetime:
        return FILE.__locally_updated_at

    # FILE methods
    async def download(FILE, _path: str = ".") -> bool:
        return_bool = False
        async with FILE.__session.get(
            f"{FILE.bin.id}/{FILE.name}",
            allow_redirects=False
        ) as response_1:
            if response_1.status in (301, 302):
                async with ClientSession() as _session:
                    if (s3_location := response_1.headers.get("Location")):
                        async with _session.get(
                            s3_location,
                            headers={
                                "Host": "s3.filebin.net",
                                "Referer": "https://filebin.net/",
                                "accept": "*/*",
                            },
                            allow_redirects=False
                        ) as response_2:
                            if response_2.status == 200:
                                with open(f"{_path}/{FILE.name}", "wb") as f:
                                    while chunk := await response_2.content.readany():
                                        f.write(chunk)
                                return_bool = True

            elif response_1.status == 403:
                raise DownloadCountReached(FILE.name)
            elif response_1.status == 404:
                raise InvalidFile(FILE.name)

        return return_bool

    async def delete(FILE) -> bool:
        return_bool = False

        async with FILE.__session.delete(
            url=f"{BASE_URL}/{FILE.bin.id}/{FILE.name}",
            headers={"Accept": "application/json"}
        ) as response:
            if response.status == 200:
                return_bool = True
            elif response.status == 404:
                InvalidBinOrFile(FILE.bin.id, FILE.name)

        return return_bool

    def __str__(FILE) -> str:
        return f"""FILE(
    name  = {FILE.name}
    bytes = {FILE.bytes}

    bin_id= {FILE.bin.id}

    hashes = {{
        sha256 = {FILE.sha256}
        md5    = {FILE.md5}
    }}
)
    """


class _QR:
    def __init__(QR, _image_bytes: bytes, _bin_id: str):
        QR.__image_bytes = _image_bytes
        QR.__bin_id = _bin_id

    @property
    def image_bytes(QR) -> bytes:
        return QR.__image_bytes

    # methods of QR
    def show(QR) -> None:
        Image.fromarray((np.array(Image.open(
            BytesIO(QR.__image_bytes))) * 255).astype('uint8')).show("bin qr")

    def save(QR, _path: str = "."):
        Image.fromarray((np.array(Image.open(BytesIO(
            QR.__image_bytes))) * 255).astype('uint8')).save(f"{_path}/{QR.__bin_id}.png")

    def __str__(QR):
        image = Image.open(BytesIO(QR.__image_bytes))

        # Resize the image to fit the console width
        console_width = 40
        aspect_ratio = image.width / image.height
        new_width = int(console_width * 0.8)
        new_height = int(new_width / aspect_ratio)
        resized_image = image.resize((new_width, new_height))

        # Convert the image to ANSI escape code sequences
        ansi_image = ""
        for y in range(resized_image.height):
            for x in range(resized_image.width):
                pixel = resized_image.getpixel((x, y))
                pixel_color = f"\x1b[48;2;{
                    abs(pixel - 1) * 255};{abs(pixel - 1) * 255};{abs(pixel - 1) * 255}m"
                ansi_image += f"{pixel_color} " * 2
            # Reset color at the end of each line
            ansi_image += "\x1b[0m\n"

        return ansi_image


# Bin
class _BIN:
    def __init__(BIN, _r: dict, _s: ClientSession):
        # setting up properties
        BIN.__session = _s

        BIN.__setProperties(_r=_r)

        BIN.__qr = None

        BIN.__locally_updated_at = datetime.now()

    # BIN property/attr private setter
    def __setProperties(BIN, _r: dict) -> None:
        r_bin = _r.get("bin", {})

        # bin properties
        BIN.__id = r_bin.get("id", None)
        BIN.__readonly = r_bin.get("readonly", None)
        BIN.__bytes = r_bin.get("bytes", None)

        # bin date time based properties
        for key in ["updated_at", "created_at", "expired_at"]:
            _dt = r_bin.get(key, None)  # Fetch the timestamp value
            if _dt is not None:
                try:
                    parsed_time = datetime.strptime(
                        _dt, "%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    try:
                        parsed_time = datetime.strptime(
                            _dt, "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        parsed_time = None  # Handle unexpected formats gracefully
            else:
                parsed_time = None

            setattr(BIN, f"__{key}", parsed_time)

        # files
        BIN.__files = [_FILE(_f=_f, _bin=BIN, _s=BIN.__session) for _f in _fs] if (
            _fs := _r.get("files", None)) is not None else []

    # BIN property/attr accessors
    @property
    def id(BIN) -> Optional[str]:
        return BIN.__id

    @property
    def readonly(BIN) -> Optional[bool]:
        return BIN.__readonly

    @property
    def bytes(BIN) -> Optional[int]:
        return BIN.__bytes

    @property
    def files(BIN) -> List[_FILE]:
        return BIN.__files

    @property
    def updated_at(BIN) -> Optional[datetime]:
        return BIN.__updated_at

    @property
    def created_at(BIN) -> Optional[datetime]:
        return BIN.__created_at

    @property
    def expired_at(BIN) -> Optional[datetime]:
        return BIN.__expired_at

    @property
    def locally_updated_at(BIN) -> datetime:
        return BIN.__locally_updated_at

    @property
    async def qr(BIN) -> _QR:
        qr = None
        if BIN.__qr:
            qr = BIN.__qr
        else:
            # TODO: changes according to new methods
            _r = await BIN.__get(f"qr/{BIN.id}", {"Accept": "image/png"})
            if _r[0] == 200:
                qr = BIN._QR(_image_bytes=_r[1], _bin_id=BIN.id)
            elif _r[0] == 404:
                raise InvalidBin(BIN.id)

        return qr

    # BIN methods
    async def update(BIN) -> _BIN:
        async with BIN.__session.get(
            url=BIN.id,
            headers={"Accept": "application/json"}
        ) as response:
            _, _r = await _response_parser(response=response)
            BIN.__setProperties(_r)
            BIN.__locally_updated_at = datetime.now()

        # returning self
        return BIN

    async def lock(BIN) -> _BIN:
        async with BIN.__session.put(url=BIN.id, headers={"Accept": "application/json"}) as response:
            _, _r = await _response_parser(response=response)
            await BIN.update()

            if BIN.readonly:
                try:
                    delattr(BIN, "uploadFile")
                except AttributeError:
                    pass
            else:
                raise "Failed to lock!"

        return BIN  # return self

    async def delete(BIN) -> bool:
        return_bool = False

        async with BIN.__session.delete(
            url=BIN.id,
            headers={"Accept": "application/json"}
        ) as response:
            if response.status == 200:
                return_bool = True
            elif response.status == 404:
                InvalidBin(BIN.id)

        return return_bool

    async def downloadArchive(BIN, _type: str, _path: str = ".") -> bool:
        return_bool = False
        if _type in ["zip", "tar"]:
            async with BIN.__session.get(
                url=f"archive/{BIN.id}/{_type}",
                headers={"accept": "application/json"}
            ) as response:
                if response.status == 200:
                    with open(f"{_path}/{BIN.id}.{_type}", "wb") as f:
                        while chunk := await response.content.readany():
                            f.write(chunk)
                    return_bool = True
                elif response.status == 404:
                    InvalidBin(BIN.id)
        else:
            raise InvalidArchiveType(_type)

        return return_bool

    async def getFile(BIN, _file_name: str, _from_cache: bool = False) -> Optional[_FILE]:
        return_file = None

        def _rf(_fn: str):
            for _f in BIN.files:
                if _f.name == _file_name:
                    return _f

        if _from_cache:
            return_file = _rf(_fn=_file_name)
        else:
            await BIN.update()
            return_file = _rf(_fn=_file_name)

        if return_file is None:
            raise InvalidFile(_file_name)

        return return_file

    async def downloadFile(BIN, _file_name: str, _path: str = ".") -> bool:
        if _f := await BIN.getFile(_file_name):
            return await _f.download(_path)

    async def deleteFile(BIN, _file_name: str) -> bool:
        return_bool = False
        if (_f := await BIN.getFile(_file_name)) and (await _f.delete()):
            BIN.files.remove(_f)
            return_bool = True

        return return_bool

    async def uploadFile(BIN, _file: str) -> Optional[_FILE]:
        return_file = None

        with open(_file, "rb") as file_data:
            _file_name = os.path.basename(_file)
            async with BIN.__session.post(
                url=f"{BIN.id}/{_file_name}",
                headers={
                    "accept": "application/json",
                    "cid": "Filebin.py",
                    "Content-Type": "application/octet-stream"
                },
                data=file_data
            ) as response:
                _s, _r = await _response_parser(response)
                if _s == 201:
                    BIN.__files.append(
                        (_f := _FILE(_f=_r.get("file"), _bin=BIN, _s=BIN.__session))
                    )
                    return_file = _f
                elif _s == 400:
                    raise InvalidBinOrFile(
                        _bin_id=BIN.id, _file_name=_file_name)
                elif _s == 403:
                    raise StorageFull(_bin_id=BIN.id)
                elif _s == 404:
                    raise LockedBin(_bin_id=BIN.id)

        return return_file

    def __hash__(BIN) -> str:
        return BIN.id

    def __str__(BIN) -> str:
        return f"""BIN(
    id        = {BIN.id}
    read_only = {BIN.readonly}
    bytes     = {BIN.bytes}

    created @ {BIN.created_at}
    updated @ {BIN.updated_at}
    expires @ {BIN.expired_at}

    files {[_f.name for _f in BIN.files]}
)
    """
