import argparse
import os
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def _validate_database(path):
    with closing(sqlite3.connect(path)) as connection:
        result = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise ValueError(f"Database integrity check failed for {path}: {result}")


def _temporary_path(destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    os.close(descriptor)
    return Path(name)


def _copy_database(source, destination):
    with closing(sqlite3.connect(source)) as source_connection, closing(
        sqlite3.connect(destination)
    ) as destination_connection:
        source_connection.backup(destination_connection)
    _validate_database(destination)
    if os.name != "nt":
        os.chmod(destination, 0o600)


def backup_database(source, destination):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if source == destination:
        raise ValueError("Backup destination must differ from the live database")
    if not source.is_file():
        raise FileNotFoundError(f"Database does not exist: {source}")
    if destination.exists():
        raise FileExistsError(f"Backup already exists: {destination}")
    temporary = _temporary_path(destination)
    try:
        _copy_database(source, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def restore_database(backup, destination):
    backup = Path(backup).resolve()
    destination = Path(destination).resolve()
    if backup == destination:
        raise ValueError("Restore source must differ from the live database")
    if not backup.is_file():
        raise FileNotFoundError(f"Backup does not exist: {backup}")
    _validate_database(backup)
    temporary = _temporary_path(destination)
    safety_copy = None
    try:
        _copy_database(backup, temporary)
        if destination.exists():
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            safety_copy = destination.with_name(f"{destination.name}.pre-restore-{timestamp}.bak")
            if safety_copy.exists():
                raise FileExistsError(f"Safety copy already exists: {safety_copy}")
            os.replace(destination, safety_copy)
        try:
            os.replace(temporary, destination)
        except OSError:
            if safety_copy and safety_copy.exists() and not destination.exists():
                os.replace(safety_copy, destination)
            raise
    finally:
        temporary.unlink(missing_ok=True)
    return destination, safety_copy


def main():
    parser = argparse.ArgumentParser(description="Create or restore a consistent SQLite database copy.")
    parser.add_argument(
        "--database",
        default=os.getenv("WARBRIDGE_DB", str(Path(__file__).resolve().parent / "warbridge.db")),
        help="Path to the WarBridge SQLite database",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    backup = commands.add_parser("backup", help="Create an integrity-checked backup")
    backup.add_argument("--output", required=True, help="Destination SQLite file")
    restore = commands.add_parser("restore", help="Restore a backup after stopping the application")
    restore.add_argument("--input", required=True, help="Source backup SQLite file")
    restore.add_argument("--confirm-restore", action="store_true", help="Confirm replacing the live database")
    args = parser.parse_args()

    if args.command == "backup":
        print(backup_database(args.database, args.output))
        return
    if not args.confirm_restore:
        parser.error("restore requires --confirm-restore")
    restored, safety_copy = restore_database(args.input, args.database)
    print(f"Restored {restored}")
    if safety_copy:
        print(f"Previous database preserved at {safety_copy}")


if __name__ == "__main__":
    main()
