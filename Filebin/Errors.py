class InvalidArchiveType(Exception):
    def __init__(self, _type: str):
        self.message = f"Invalid Archive Type, {_type!r}"
        super().__init__(self.message)


class InvalidBin(Exception):
    def __init__(self, _id: str):
        self.message = f"Invalid Bin Id, {_id!r}"
        super().__init__(self.message)


class InvalidFile(Exception):
    def __init__(self, _file_name: str):
        self.message = f"Invalid File, {_file_name!r}"
        super().__init__(self.message)


class InvalidBinOrFile(Exception):
    def __init__(self, _bin_id: str, _file_name: str):
        self.message = f"""Invalid Bin or File, {f"{_bin_id}/{_file_name}"!r}"""
        super().__init__(self.message)


class DownloadCountReached(Exception):
    def __init__(self, _file_name: str):
        self.message = f"Download Count Reached!, {_file_name!r}"
        super().__init__(self.message)


class StorageFull(Exception):
    def __init__(self, _bin_id: str):
        self.message = f"""Bin Storage Full!, {_bin_id!r}"""
        super().__init__(self.message)


class LockedBin(Exception):
    def __init__(self, _bin_id: str):
        self.message = f"""Bin is Locked!, {_bin_id!r}"""
        super().__init__(self.message)
