import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from db_backup import backup_database, restore_database


class DatabaseBackupTests(unittest.TestCase):
    def test_backup_and_restore_preserve_a_valid_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = root / "warbridge.db"
            backup = root / "backups" / "warbridge.sqlite3"
            with closing(sqlite3.connect(live)) as connection:
                connection.execute("CREATE TABLE examples(value TEXT NOT NULL)")
                connection.execute("INSERT INTO examples(value) VALUES('before')")
                connection.commit()

            backup_database(live, backup)
            with closing(sqlite3.connect(live)) as connection:
                connection.execute("UPDATE examples SET value='after'")
                connection.commit()

            restored, safety_copy = restore_database(backup, live)
            self.assertEqual(restored, live.resolve())
            self.assertTrue(safety_copy and safety_copy.is_file())
            with closing(sqlite3.connect(live)) as connection:
                value = connection.execute("SELECT value FROM examples").fetchone()[0]
            self.assertEqual(value, "before")
            with closing(sqlite3.connect(safety_copy)) as connection:
                previous_value = connection.execute("SELECT value FROM examples").fetchone()[0]
            self.assertEqual(previous_value, "after")

    def test_backup_refuses_to_overwrite_the_live_database(self):
        with tempfile.TemporaryDirectory() as directory:
            live = Path(directory) / "warbridge.db"
            with closing(sqlite3.connect(live)) as connection:
                connection.execute("CREATE TABLE examples(value TEXT)")
            with self.assertRaises(ValueError):
                backup_database(live, live)


if __name__ == "__main__":
    unittest.main()
