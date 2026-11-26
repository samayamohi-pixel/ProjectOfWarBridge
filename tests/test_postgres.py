import os
import subprocess
import sys
import unittest
import uuid
from pathlib import Path


class DatabaseSafetyTests(unittest.TestCase):
    def test_test_database_rejects_production_url_alias(self):
        env = os.environ.copy()
        for key in (
            "WARBRIDGE_TEST_DATABASE_URL",
            "WARBRIDGE_DATABASE_URL",
            "DATABASE_URL",
        ):
            env.pop(key, None)
        env.update(
            WARBRIDGE_ENV="test",
            WARBRIDGE_TEST_DATABASE_URL="postgresql://user@localhost/warbridge",
            WARBRIDGE_DATABASE_URL="postgres://user@localhost/warbridge",
        )
        result = subprocess.run(
            [sys.executable, "-c", "import database"],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be separate", result.stderr)


@unittest.skipUnless(
    os.getenv("WARBRIDGE_TEST_DATABASE_URL"),
    "Set WARBRIDGE_TEST_DATABASE_URL to run PostgreSQL integration tests",
)
class PostgreSQLIntegrationTests(unittest.TestCase):
    def test_schema_migrations_indexes_and_existing_rows(self):
        os.environ["WARBRIDGE_ENV"] = "test"
        from app import app, get_db, init_db, utcnow

        with app.app_context():
            init_db()
            db = get_db()
            suffix = uuid.uuid4().hex
            cursor = db.execute(
                """INSERT INTO users(name,email,password_hash,role,verified,created_at)
                   VALUES(?,?,?,?,1,?)""",
                (
                    "PostgreSQL integration",
                    f"{suffix}@example.test",
                    "unused",
                    "DISPLACED",
                    utcnow(),
                ),
            )
            user_id = cursor.lastrowid
            db.commit()

            init_db()
            self.assertEqual(
                get_db().execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone()["id"],
                user_id,
            )
            self.assertEqual(
                get_db().execute(
                    "SELECT MAX(version) AS version FROM schema_migrations"
                ).fetchone()["version"],
                3,
            )
            indexes = {
                row["indexname"]
                for row in get_db().execute(
                    "SELECT indexname FROM pg_indexes WHERE schemaname=current_schema()"
                ).fetchall()
            }
            self.assertTrue(
                {
                    "idx_users_email",
                    "idx_help_requests_status",
                    "idx_help_requests_sos_status",
                    "idx_shelters_verification_block",
                    "idx_accommodations_verification_block",
                    "idx_services_verification_block",
                    "idx_alerts_expires_at",
                    "idx_audit_log_created_at",
                }.issubset(indexes)
            )
            get_db().commit()


if __name__ == "__main__":
    unittest.main()
