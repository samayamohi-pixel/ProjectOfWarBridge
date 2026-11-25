import os
import tempfile
import unittest


fd, db_path = tempfile.mkstemp()
os.close(fd)
os.environ["WARBRIDGE_DB"] = db_path
os.environ["SECRET_KEY"] = "test-secret"

from app import app, get_db, utcnow
from werkzeug.security import generate_password_hash


class WarBridgeApiTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        csrf = self.client.get("/api/csrf").get_json()["csrfToken"]
        self.csrf = {"X-CSRF-Token": csrf}

    def test_public_resources_are_available(self):
        self.assertEqual(self.client.get("/api/public/alerts").status_code, 200)
        self.assertEqual(self.client.get("/api/public/shelters").status_code, 200)

    def test_register_login_and_logout(self):
        result = self.client.post(
            "/api/auth/register",
            headers=self.csrf,
            json={"name": "Helping Foundation", "email": "test@example.com", "password": "strongpass", "role": "NGO"},
        )
        self.assertEqual(result.status_code, 200)
        self.assertNotIn("password_hash", result.get_json()["user"])
        token = result.get_json()["csrfToken"]
        logout = self.client.post("/api/auth/logout", headers={"X-CSRF-Token": token})
        self.assertEqual(logout.status_code, 200)
        csrf = self.client.get("/api/csrf").get_json()["csrfToken"]
        login = self.client.post(
            "/api/auth/login",
            headers={"X-CSRF-Token": csrf},
            json={"identity": "Helping Foundation", "password": "strongpass", "role": "NGO"},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.get_json()["user"]["role"], "NGO")

    def test_role_scoped_admin_login_and_wrong_password(self):
        with app.app_context():
            get_db().execute(
                """INSERT INTO users(name,email,password_hash,role,verified,created_at)
                   VALUES(?,?,?,?,1,?)""",
                ("Root Admin", "root@example.com", generate_password_hash("correct-horse-battery"), "ADMIN", utcnow()),
            )
            get_db().commit()
        wrong_role = self.client.post(
            "/api/auth/login",
            headers=self.csrf,
            json={"identity": "Root Admin", "password": "correct-horse-battery", "role": "NGO"},
        )
        self.assertEqual(wrong_role.status_code, 401)
        csrf = self.client.get("/api/csrf").get_json()["csrfToken"]
        wrong_password = self.client.post(
            "/api/auth/login",
            headers={"X-CSRF-Token": csrf},
            json={"identity": "Root Admin", "password": "incorrect-password", "role": "ADMIN"},
        )
        self.assertEqual(wrong_password.status_code, 401)
        csrf = self.client.get("/api/csrf").get_json()["csrfToken"]
        login = self.client.post(
            "/api/auth/login",
            headers={"X-CSRF-Token": csrf},
            json={"identity": "Root Admin", "password": "correct-horse-battery", "role": "ADMIN"},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.get_json()["user"]["role"], "ADMIN")

    def test_sos_accepts_honeypot_and_requires_csrf(self):
        missing = self.client.post("/api/sos", json={"location": "Test"})
        self.assertEqual(missing.status_code, 403)
        result = self.client.post(
            "/api/sos",
            headers=self.csrf,
            json={"location": "Test", "phone": "", "website": "", "_csrf": self.csrf["X-CSRF-Token"]},
        )
        self.assertEqual(result.status_code, 200)


if __name__ == "__main__":
    unittest.main()
