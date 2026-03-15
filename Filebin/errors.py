class FilebinError(Exception):
    """Base class for all Filebin library exceptions."""


class InvalidArchiveType(FilebinError):
    def __init__(self, archive_type: str):
        self.message = f"Invalid archive type: {archive_type!r}. Expected 'zip' or 'tar'."
        super().__init__(self.message)


class InvalidBin(FilebinError):
    def __init__(self, bin_id: str):
        self.message = f"Bin not found: {bin_id!r}"
        super().__init__(self.message)


class InvalidFile(FilebinError):
    def __init__(self, file_name: str):
        self.message = f"File not found in bin: {file_name!r}"
        super().__init__(self.message)


class InvalidBinOrFile(FilebinError):
    def __init__(self, bin_id: str, file_name: str):
        self.message = f"Invalid bin or file: {bin_id!r}/{file_name!r}"
        super().__init__(self.message)


class DownloadCountReached(FilebinError):
    def __init__(self, file_name: str):
        self.message = f"Download count limit reached for file: {file_name!r}"
        super().__init__(self.message)


class StorageFull(FilebinError):
    def __init__(self, bin_id: str):
        self.message = f"Storage is full for bin: {bin_id!r}"
        super().__init__(self.message)


class LockedBin(FilebinError):
    def __init__(self, bin_id: str):
        self.message = f"Bin is locked (read-only): {bin_id!r}"
        super().__init__(self.message)


class LockFailed(FilebinError):
    def __init__(self, bin_id: str):
        self.message = f"Failed to lock bin: {bin_id!r}"
        super().__init__(self.message)
