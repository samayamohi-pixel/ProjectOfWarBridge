import os
import secrets
import tempfile
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor


fd, db_path = tempfile.mkstemp()
os.close(fd)
os.environ["WARBRIDGE_DB"] = db_path
os.environ["SECRET_KEY"] = "test-secret"
os.environ["WARBRIDGE_ENV"] = "test"

from app import app, get_db, utcnow
from werkzeug.security import generate_password_hash


class WarBridgeApiTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        csrf = self.client.get("/api/csrf").get_json()["csrfToken"]
        self.csrf = {"X-CSRF-Token": csrf}
        with app.app_context():
            get_db().execute("DELETE FROM rate_limit_events")
            get_db().commit()

    def create_user(self, role, verified=True):
        suffix = uuid.uuid4().hex
        with app.app_context():
            cur = get_db().execute(
                """INSERT INTO users(name,email,password_hash,role,verified,created_at)
                   VALUES(?,?,?,?,?,?)""",
                (f"Test {role} {suffix}", f"{suffix}@example.test", "unused", role, int(verified), utcnow()),
            )
            get_db().commit()
            return cur.lastrowid

    def authenticate(self, user_id):
        token = secrets.token_urlsafe(32)
        with self.client.session_transaction() as session:
            session.clear()
            session["user_id"] = user_id
            session["csrf_token"] = token
        self.csrf = {"X-CSRF-Token": token}

    def create_shelter(self, ngo_id, beds=1):
        with app.app_context():
            cur = get_db().execute(
                """INSERT INTO shelters(ngo_id,name,city,area,beds_available,verified,updated_at)
                   VALUES(?,?,?,?,?,1,?)""",
                (ngo_id, f"Shelter {uuid.uuid4().hex}", "Test City", "Test Area", beds, utcnow()),
            )
            get_db().commit()
            return cur.lastrowid

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
        self.assertEqual(result.status_code, 201)

    def test_sos_queue_redacts_details_until_verified_ngo_claims(self):
        result = self.client.post(
            "/api/sos",
            headers=self.csrf,
            json={"name": "Caller", "phone": "555-0101", "location": "Exact address"},
        )
        self.assertEqual(result.status_code, 201)
        request_id = result.get_json()["id"]

        ngo_id = self.create_user("NGO")
        self.authenticate(ngo_id)
        queued = next(
            item for item in self.client.get("/api/sos/incoming").get_json()["requests"]
            if item["id"] == request_id
        )
        self.assertTrue(queued["has_contact"])
        self.assertTrue(queued["has_location"])
        self.assertNotIn("contact", queued)
        self.assertNotIn("location_text", queued)
        self.assertNotIn("requester_name", queued)

        claimed = self.client.post(f"/api/sos/{request_id}/claim", headers=self.csrf)
        self.assertEqual(claimed.status_code, 200)
        claimed_row = next(
            item for item in self.client.get("/api/sos/incoming").get_json()["requests"]
            if item["id"] == request_id
        )
        self.assertEqual(claimed_row["contact"], "555-0101")
        self.assertEqual(claimed_row["location_text"], "Exact address")
        self.assertEqual(claimed_row["requester_name"], "Caller")
        with app.app_context():
            audited = get_db().execute(
                """SELECT 1 FROM audit_log
                   WHERE action='sos_details_accessed' AND target_id=? AND actor_id=?""",
                (request_id, ngo_id),
            ).fetchone()
        self.assertIsNotNone(audited)

        resolved = self.client.post(f"/api/sos/{request_id}/resolve", headers=self.csrf)
        self.assertEqual(resolved.status_code, 200)
        self.assertNotIn(
            request_id,
            [item["id"] for item in self.client.get("/api/sos/incoming").get_json()["requests"]],
        )

    def test_unverified_ngo_cannot_read_or_claim_sos(self):
        result = self.client.post("/api/sos", headers=self.csrf, json={"location": "Test"})
        self.assertEqual(result.status_code, 201)
        ngo_id = self.create_user("NGO", verified=False)
        self.authenticate(ngo_id)
        self.assertEqual(self.client.get("/api/sos/incoming").status_code, 403)
        self.assertEqual(
            self.client.post(f"/api/sos/{result.get_json()['id']}/claim", headers=self.csrf).status_code,
            403,
        )

    def test_pending_request_details_are_hidden_until_acceptance(self):
        ngo_id = self.create_user("NGO")
        shelter_id = self.create_shelter(ngo_id)
        displaced_id = self.create_user("DISPLACED")
        with app.app_context():
            cur = get_db().execute(
                """INSERT INTO help_requests(requester_id,shelter_id,type,contact,location_text,status,updated_at,created_at)
                   VALUES(?,?, 'shelter','555-0102','Private location','Pending',?,?)""",
                (displaced_id, shelter_id, utcnow(), utcnow()),
            )
            get_db().commit()
            request_id = cur.lastrowid

        self.authenticate(ngo_id)
        pending = self.client.get("/api/requests/incoming").get_json()["requests"][0]
        self.assertNotIn("contact", pending)
        self.assertNotIn("location_text", pending)
        accepted = self.client.post(f"/api/requests/{request_id}/accept", headers=self.csrf)
        self.assertEqual(accepted.status_code, 200)
        visible = self.client.get("/api/requests/incoming").get_json()["requests"][0]
        self.assertEqual(visible["contact"], "555-0102")
        self.assertEqual(visible["location_text"], "Private location")

    def test_accommodation_capacity_is_reserved_and_restored(self):
        host_id = self.create_user("HOST")
        displaced_id = self.create_user("DISPLACED")
        with app.app_context():
            cur = get_db().execute(
                """INSERT INTO accommodations(host_id,city,area,rooms,rooms_available,verified,updated_at)
                   VALUES(?,'Test City','Test Area',1,1,1,?)""",
                (host_id, utcnow()),
            )
            get_db().commit()
            accommodation_id = cur.lastrowid

        self.authenticate(displaced_id)
        request_result = self.client.post(
            "/api/requests",
            headers=self.csrf,
            json={"type": "accommodation", "accommodation_id": accommodation_id},
        )
        self.assertEqual(request_result.status_code, 201)
        request_id = request_result.get_json()["request"]["id"]

        self.authenticate(host_id)
        accepted = self.client.post(f"/api/requests/{request_id}/accept", headers=self.csrf)
        self.assertEqual(accepted.status_code, 200)
        with app.app_context():
            available = get_db().execute(
                "SELECT rooms_available FROM accommodations WHERE id=?", (accommodation_id,)
            ).fetchone()["rooms_available"]
        self.assertEqual(available, 0)

        self.authenticate(displaced_id)
        unavailable = self.client.post(
            "/api/requests",
            headers=self.csrf,
            json={"type": "accommodation", "accommodation_id": accommodation_id},
        )
        self.assertEqual(unavailable.status_code, 409)
        self.authenticate(host_id)
        completed = self.client.post(f"/api/requests/{request_id}/complete", headers=self.csrf)
        self.assertEqual(completed.status_code, 200)
        with app.app_context():
            available = get_db().execute(
                "SELECT rooms_available FROM accommodations WHERE id=?", (accommodation_id,)
            ).fetchone()["rooms_available"]
        self.assertEqual(available, 1)

    def test_concurrent_acceptance_cannot_overbook_last_room(self):
        host_id = self.create_user("HOST")
        displaced_ids = [self.create_user("DISPLACED"), self.create_user("DISPLACED")]
        with app.app_context():
            cur = get_db().execute(
                """INSERT INTO accommodations(host_id,city,area,rooms,rooms_available,verified,updated_at)
                   VALUES(?,'Test City','Test Area',1,1,1,?)""",
                (host_id, utcnow()),
            )
            accommodation_id = cur.lastrowid
            request_ids = []
            for displaced_id in displaced_ids:
                request = get_db().execute(
                    """INSERT INTO help_requests(requester_id,accommodation_id,type,status,updated_at,created_at)
                       VALUES(?,?,'accommodation','Pending',?,?)""",
                    (displaced_id, accommodation_id, utcnow(), utcnow()),
                )
                request_ids.append(request.lastrowid)
            get_db().commit()

        barrier = threading.Barrier(2)

        def accept(request_id):
            client = app.test_client()
            token = secrets.token_urlsafe(32)
            with client.session_transaction() as session:
                session["user_id"] = host_id
                session["csrf_token"] = token
            barrier.wait()
            return client.post(
                f"/api/requests/{request_id}/accept",
                headers={"X-CSRF-Token": token},
            ).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(accept, request_ids))
        self.assertCountEqual(statuses, [200, 409])
        with app.app_context():
            available = get_db().execute(
                "SELECT rooms_available FROM accommodations WHERE id=?", (accommodation_id,)
            ).fetchone()["rooms_available"]
        self.assertEqual(available, 0)

    def test_service_rating_requires_a_completed_interaction(self):
        displaced_id = self.create_user("DISPLACED")
        self.authenticate(displaced_id)
        response = self.client.post(
            "/api/ratings",
            headers=self.csrf,
            json={"listing_type": "service", "listing_id": 1, "stars": 5},
        )
        self.assertEqual(response.status_code, 403)

    def test_listing_requires_admin_approval_and_reports_require_a_target(self):
        ngo_id = self.create_user("NGO")
        with app.app_context():
            cur = get_db().execute(
                """INSERT INTO shelters(ngo_id,name,city,area,beds_available,verified,updated_at)
                   VALUES(?,'Pending Review Shelter','Review City','Review Area',2,0,?)""",
                (ngo_id, utcnow()),
            )
            get_db().commit()
            shelter_id = cur.lastrowid

        admin_id = self.create_user("ADMIN")
        self.authenticate(admin_id)
        pending = self.client.get("/api/admin/listings/pending").get_json()["listings"]
        self.assertIn(shelter_id, [item["id"] for item in pending if item["listing_type"] == "shelter"])
        approved = self.client.post(
            f"/api/admin/listings/shelter/{shelter_id}/approve",
            headers=self.csrf,
        )
        self.assertEqual(approved.status_code, 200)
        public_ids = [item["id"] for item in self.client.get("/api/public/shelters").get_json()["shelters"]]
        self.assertIn(shelter_id, public_ids)

        reporter_id = self.create_user("DISPLACED")
        self.authenticate(reporter_id)
        invalid_report = self.client.post(
            "/api/reports",
            headers=self.csrf,
            json={"listing_type": "shelter", "listing_id": 999999, "reason": "Not a real listing"},
        )
        self.assertEqual(invalid_report.status_code, 404)


if __name__ == "__main__":
    unittest.main()
