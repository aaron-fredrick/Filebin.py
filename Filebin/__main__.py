"""
Filebin CLI — interact with Filebin.net from the command line.

Usage:
    python -m Filebin <command> [args]
    filebin <command> [args]       # if installed via pip

Commands:
    bin     <bin_id>                    Show bin info
    upload  <bin_id> <file>             Upload a file to a bin
    download <bin_id> <file> [--path]   Download a file from a bin
    archive  <bin_id> zip|tar [--path]  Download entire bin as archive
    delete-file <bin_id> <file>         Delete a file from a bin
    delete-bin  <bin_id>                Delete an entire bin
    lock    <bin_id>                    Lock a bin (make read-only)
"""

import argparse
import asyncio
import sys

from . import API
from .errors import FilebinError


def _buildParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="filebin",
        description="Interact with Filebin.net from the command line.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # -- bin info --
    p_bin = sub.add_parser("bin", help="Show bin info")
    p_bin.add_argument("bin_id", metavar="<bin_id>")

    # -- upload --
    p_upload = sub.add_parser("upload", help="Upload a file to a bin")
    p_upload.add_argument("bin_id", metavar="<bin_id>")
    p_upload.add_argument("file", metavar="<file>", help="Local file path to upload")

    # -- download --
    p_dl = sub.add_parser("download", help="Download a file from a bin")
    p_dl.add_argument("bin_id", metavar="<bin_id>")
    p_dl.add_argument("file", metavar="<file>", help="Filename to download")
    p_dl.add_argument(
        "--path", default=".", metavar="<dir>", help="Directory to save the file (default: .)"
    )

    # -- archive --
    p_arc = sub.add_parser("archive", help="Download the entire bin as a zip or tar archive")
    p_arc.add_argument("bin_id", metavar="<bin_id>")
    p_arc.add_argument("type", metavar="zip|tar", choices=["zip", "tar"])
    p_arc.add_argument(
        "--path", default=".", metavar="<dir>", help="Directory to save the archive (default: .)"
    )

    # -- delete-file --
    p_df = sub.add_parser("delete-file", help="Delete a single file from a bin")
    p_df.add_argument("bin_id", metavar="<bin_id>")
    p_df.add_argument("file", metavar="<file>", help="Filename to delete")

    # -- delete-bin --
    p_db = sub.add_parser("delete-bin", help="Delete an entire bin")
    p_db.add_argument("bin_id", metavar="<bin_id>")

    # -- lock --
    p_lock = sub.add_parser("lock", help="Lock a bin (make it read-only)")
    p_lock.add_argument("bin_id", metavar="<bin_id>")

    return parser


async def _run(args: argparse.Namespace) -> int:
    async with API() as api:
        if args.command == "bin":
            bin = await api.getBin(args.bin_id)
            print(bin)

        elif args.command == "upload":
            bin = await api.getBin(args.bin_id)
            file = await bin.uploadFile(args.file)
            print(f"Uploaded: {file.name}  ({file.bytes} bytes)")

        elif args.command == "download":
            ok = await api.getFile(args.bin_id, args.file)
            downloaded = await ok.download(args.path)
            if downloaded:
                print(f"Saved: {args.path}/{args.file}")
            else:
                print("Download failed.", file=sys.stderr)
                return 1

        elif args.command == "archive":
            ok = await api.downloadArchivedBin(args.bin_id, args.type, args.path)
            if ok:
                print(f"Saved: {args.path}/{args.bin_id}.{args.type}")
            else:
                print("Archive download failed.", file=sys.stderr)
                return 1

        elif args.command == "delete-file":
            bin = await api.getBin(args.bin_id)
            deleted = await bin.deleteFile(args.file)
            if deleted:
                print(f"Deleted file: {args.file}")
            else:
                print("Delete failed.", file=sys.stderr)
                return 1

        elif args.command == "delete-bin":
            deleted = await api.deleteBin(args.bin_id)
            if deleted:
                print(f"Deleted bin: {args.bin_id}")
            else:
                print("Delete failed.", file=sys.stderr)
                return 1

        elif args.command == "lock":
            bin = await api.lockBin(args.bin_id)
            print(f"Locked bin: {bin.id}")

    return 0


def main() -> None:
    parser = _buildParser()
    args = parser.parse_args()

    try:
        code = asyncio.run(_run(args))
        sys.exit(code)
    except FilebinError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
