# Filebin.py

<div align="center">

[![PyPI status](https://img.shields.io/pypi/v/Filebin.py)](https://pypi.org/project/Filebin.py/)
[![CI status](https://github.com/aaron-fredrick/Filebin.py/actions/workflows/ci.yml/badge.svg)](https://github.com/aaron-fredrick/Filebin.py/actions/workflows/ci.yml)
[![CodeQL status](https://github.com/aaron-fredrick/Filebin.py/actions/workflows/codeql.yml/badge.svg)](https://github.com/aaron-fredrick/Filebin.py/actions/workflows/codeql.yml)
[![License status](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

</div>

An async Python library and CLI for [Filebin.net](https://filebin.net) — upload, download, and manage file bins programmatically or from your terminal.

---

## Installation

```bash
pip install Filebin.py
```

Requires Python 3.10+.

---

## Library Usage

### Async Context Manager (recommended)

```python
import asyncio
from Filebin import API

async def main():
    async with API() as api:
        # Fetch a bin
        bin = await api.getBin("my-bin-id")
        print(bin)

        # Upload a file
        file = await bin.uploadFile("report.pdf")
        print(f"Uploaded: {file.name} ({file.bytes} bytes)")

        # Download a specific file
        await bin.downloadFile("report.pdf", path="./downloads")

        # Download entire bin as a zip archive
        await api.downloadArchivedBin("my-bin-id", "zip", path="./downloads")

        # Delete a file from a bin
        await bin.deleteFile("report.pdf")

        # Lock a bin (makes it read-only)
        await api.lockBin("my-bin-id")

        # Delete a bin
        await api.deleteBin("my-bin-id")

asyncio.run(main())
```

### Manual Session

```python
api = API()
await api.start()
bin = await api.getBin("my-bin-id")
await api.close()
```

### Caching

Both `getBin` and `getFile` accept a `from_cache=True` flag to skip the network request and return the locally cached object:

```python
bin = await api.getBin("my-bin-id", from_cache=True)
```

---

## CLI Usage

After installing, a `filebin` command is available in your shell.

```
Usage: filebin <command> [args]
       python -m Filebin <command> [args]
```

### Commands

| Command | Description |
|---------|-------------|
| `bin <bin_id>` | Show bin info (id, size, files, expiry) |
| `upload <bin_id> <file>` | Upload a local file to a bin |
| `download <bin_id> <file> [--path <dir>]` | Download a file from a bin |
| `archive <bin_id> zip\|tar [--path <dir>]` | Download entire bin as zip or tar |
| `delete-file <bin_id> <file>` | Delete a file from a bin |
| `delete-bin <bin_id>` | Delete an entire bin |
| `lock <bin_id>` | Lock a bin (make it read-only) |

### Examples

```bash
# Show bin info
filebin bin zlpiruayaav16ra2

# Upload a file
filebin upload my-bin-id photo.jpg

# Download a file to ./downloads
filebin download my-bin-id photo.jpg --path ./downloads

# Download the whole bin as a zip
filebin archive my-bin-id zip --path ./downloads

# Delete a single file
filebin delete-file my-bin-id photo.jpg

# Lock a bin
filebin lock my-bin-id
```

---

## API Reference

### `API`

| Method | Returns | Description |
|--------|---------|-------------|
| `getBin(bin_id, from_cache=False)` | `Bin` | Fetch a bin by ID |
| `lockBin(bin_id)` | `Bin` | Lock a bin |
| `deleteBin(bin_id)` | `bool` | Delete a bin |
| `downloadArchivedBin(bin_id, type, path)` | `bool` | Download zip/tar archive |
| `getFile(bin_id, file_name, from_cache=False)` | `File` | Fetch a file by name |

### `Bin`

| Property / Method | Description |
|-------------------|-------------|
| `id`, `readonly`, `bytes` | Core bin metadata |
| `created_at`, `updated_at`, `expired_at` | Timestamps |
| `files` | `List[File]` — cached file list |
| `uploadFile(file_path)` | Upload a local file |
| `downloadFile(file_name, path)` | Download a file |
| `deleteFile(file_name)` | Delete a file |
| `downloadArchive(type, path)` | Download as zip or tar |
| `lock()` | Make read-only |
| `delete()` | Delete the bin |
| `update()` | Refresh from server |

### `File`

| Property | Description |
|----------|-------------|
| `name`, `bytes`, `content_type` | File metadata |
| `md5`, `sha256` | Integrity hashes |
| `created_at`, `updated_at` | Timestamps |
| `bin` | Parent `Bin` reference |
| `download(path)` | Download to a local directory |
| `delete()` | Delete this file |

---

## Exceptions

All exceptions inherit from `FilebinError`:

| Exception | Raised when |
|-----------|-------------|
| `InvalidBin` | Bin ID not found (404) |
| `InvalidFile` | File not found in bin |
| `InvalidBinOrFile` | Upload rejected (400) |
| `InvalidArchiveType` | Archive type is not `zip` or `tar` |
| `DownloadCountReached` | File download limit hit (403) |
| `StorageFull` | Bin storage limit reached |
| `LockedBin` | Bin is read-only, upload rejected |
| `LockFailed` | Lock operation did not take effect |

```python
from Filebin.errors import FilebinError, InvalidBin, InvalidFile

try:
    bin = await api.getBin("bad-id")
except InvalidBin as e:
    print(e.message)
except FilebinError as e:
    print(f"Filebin error: {e}")
```

---

## Development

```bash
# Clone and install with dev dependencies
git clone https://github.com/aaron-fredrick/Filebin.py
pip install -e ".[dev]"

# Run offline unit tests
pytest -m "not network" -v

# Run all tests (requires network)
pytest -v

# Lint
ruff check Filebin/ tests/
```

### CI

- **`ci.yml`** — runs on every push and PR to `main`: lint + unit tests across Python 3.10–3.13.
- **`release.yml`** — triggered by `v*` tags: tests → build → publish to PyPI via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/).

---

## License

MIT © [Aaron Fredrick](https://github.com/aaron-fredrick)

---

## 💖 Support the Project
If you find Filebin.py useful, please consider supporting its development:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/aaronfredrick)
