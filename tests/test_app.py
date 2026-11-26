import os
import secrets
import tempfile
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import patch


fd, db_path = tempfile.mkstemp()
os.close(fd)
os.environ["WARBRIDGE_DB"] = db_path
os.environ["SECRET_KEY"] = "test-secret"
os.environ["WARBRIDGE_ENV"] = "test"

from app import app, get_db, init_db, normalize_origin, utcnow
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

    def test_schema_migrations_preserve_existing_users(self):
        user_id = self.create_user("DISPLACED")
        with app.app_context():
            init_db()
            db = get_db()
            self.assertEqual(
                db.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone()["id"],
                user_id,
            )
            self.assertEqual(
                db.execute(
                    "SELECT MAX(version) AS version FROM schema_migrations"
                ).fetchone()["version"],
                3,
            )

    def test_admin_analytics_requires_admin_role(self):
        self.assertEqual(self.client.get("/api/admin/analytics").status_code, 401)

        displaced_id = self.create_user("DISPLACED")
        self.authenticate(displaced_id)
        self.assertEqual(self.client.get("/api/admin/analytics").status_code, 403)

        admin_id = self.create_user("ADMIN")
        self.authenticate(admin_id)
        response = self.client.get("/api/admin/analytics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("users", response.get_json())

    def test_admin_analytics_aggregates_platform_metrics_and_periods(self):
        admin_id = self.create_user("ADMIN")
        self.authenticate(admin_id)
        baseline_response = self.client.get("/api/admin/analytics")
        self.assertEqual(baseline_response.status_code, 200)
        baseline = baseline_response.get_json()

        ngo_id = self.create_user("NGO")
        pending_ngo_id = self.create_user("NGO", verified=False)
        host_id = self.create_user("HOST")
        pending_host_id = self.create_user("HOST", verified=False)
        resident_id = self.create_user("DISPLACED")
        shelter_id = self.create_shelter(ngo_id, beds=4)
        now = datetime.now(timezone.utc)
        created_at = (now - timedelta(days=1)).isoformat()
        completed_at = (now - timedelta(hours=12)).isoformat()
        sos_created_at = (now - timedelta(minutes=10)).isoformat()
        sos_claimed_at = (now - timedelta(minutes=8)).isoformat()

        with app.app_context():
            db = get_db()
            accommodation = db.execute(
                """INSERT INTO accommodations(
                       host_id,city,area,rooms,rooms_available,verified,updated_at
                   ) VALUES(?,?,?,?,?,1,?)""",
                (host_id, "Test City", "Test Area", 2, 2, utcnow()),
            )
            db.execute(
                """INSERT INTO shelters(
                       ngo_id,name,city,area,beds_available,verified,updated_at
                   ) VALUES(?,?,?,?,?,0,?)""",
                (pending_ngo_id, "Pending Shelter", "Test City", "Test Area", 2, utcnow()),
            )
            db.execute(
                """INSERT INTO services(
                       ngo_id,name,category,city,verified,blocked,closed,updated_at
                   ) VALUES(?,?,?,?,1,1,0,?)""",
                (ngo_id, "Blocked Service", "Food", "Test City", utcnow()),
            )
            db.execute(
                """INSERT INTO accommodations(
                       host_id,city,area,rooms,rooms_available,verified,updated_at
                   ) VALUES(?,?,?,?,?,0,?)""",
                (pending_host_id, "Test City", "Pending Area", 1, 1, utcnow()),
            )

            for status in ("Pending", "Accepted", "Completed", "Rejected", "Cancelled"):
                updated_at = completed_at if status == "Completed" else created_at
                db.execute(
                    """INSERT INTO help_requests(
                           requester_id,shelter_id,type,status,updated_at,created_at
                       ) VALUES(?,?, 'shelter',?,?,?)""",
                    (resident_id, shelter_id, status, updated_at, created_at),
                )
            db.execute(
                """INSERT INTO help_requests(
                       type,requester_name,contact,location_text,status,is_sos,
                       claimed_by,claimed_at,updated_at,created_at
                   ) VALUES('SOS','Demo Caller','000-000-0000','Test Area',
                            'Accepted',1,?,?,?,?)""",
                (ngo_id, sos_claimed_at, sos_claimed_at, sos_created_at),
            )
            db.execute(
                """INSERT INTO help_requests(
                       type,requester_name,contact,location_text,status,is_sos,
                       updated_at,created_at
                   ) VALUES('SOS','Demo Caller','000-000-0000','Test Area',
                            'Pending',1,?,?)""",
                (sos_created_at, sos_created_at),
            )
            db.execute(
                """INSERT INTO reports(
                       reporter_id,listing_type,listing_id,reason,status,updated_at,created_at
                   ) VALUES(?,?,?,'Test report','Open',?,?)""",
                (resident_id, "shelter", shelter_id, utcnow(), utcnow()),
            )
            db.commit()

        result_response = self.client.get("/api/admin/analytics")
        self.assertEqual(result_response.status_code, 200)
        result = result_response.get_json()
        self.assertEqual(result["users"]["total"], baseline["users"]["total"] + 5)
        self.assertEqual(
            result["users"]["by_role"]["DISPLACED"],
            baseline["users"]["by_role"]["DISPLACED"] + 1,
        )
        self.assertEqual(result["users"]["partners"]["NGO"]["verified"], baseline["users"]["partners"]["NGO"]["verified"] + 1)
        self.assertEqual(result["users"]["partners"]["NGO"]["pending"], baseline["users"]["partners"]["NGO"]["pending"] + 1)
        self.assertEqual(result["users"]["partners"]["HOST"]["verified"], baseline["users"]["partners"]["HOST"]["verified"] + 1)
        self.assertEqual(result["users"]["partners"]["HOST"]["pending"], baseline["users"]["partners"]["HOST"]["pending"] + 1)
        for status in ("pending", "accepted", "completed", "rejected", "cancelled"):
            self.assertEqual(
                result["requests"]["by_status"][status],
                baseline["requests"]["by_status"][status] + 1,
            )
        self.assertEqual(result["listings"]["available_shelter_beds"], baseline["listings"]["available_shelter_beds"] + 4)
        self.assertEqual(result["listings"]["available_accommodation_rooms"], baseline["listings"]["available_accommodation_rooms"] + 2)
        self.assertEqual(result["listings"]["open_reports"], baseline["listings"]["open_reports"] + 1)
        self.assertEqual(result["listings"]["blocked"], baseline["listings"]["blocked"] + 1)
        self.assertEqual(result["listings"]["pending"], baseline["listings"]["pending"] + 2)
        self.assertEqual(result["sos"]["unresolved"], baseline["sos"]["unresolved"] + 2)
        self.assertEqual(result["sos"]["response_count"], baseline["sos"]["response_count"] + 1)
        self.assertAlmostEqual(result["sos"]["average_response_seconds"], 120, delta=1)
        self.assertTrue(result["has_activity"])
        for period in ("last_7_days", "last_30_days", "last_90_days"):
            self.assertEqual(result["requests"]["periods"][period]["created"], baseline["requests"]["periods"][period]["created"] + 5)
            self.assertEqual(result["requests"]["periods"][period]["completed"], baseline["requests"]["periods"][period]["completed"] + 1)

    def test_preview_security_headers_use_explicit_embedding_allowlists(self):
        with patch("app.FRAME_ANCESTORS", ("'self'", "https://preview.example")), patch(
            "app.ALLOWED_CORS_ORIGINS", ("https://preview.example",)
        ):
            response = self.client.options(
                "/api/csrf",
                headers={
                    "Origin": "https://preview.example",
                    "Access-Control-Request-Method": "POST",
                },
            )
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "https://preview.example")
        self.assertEqual(response.headers["Access-Control-Allow-Credentials"], "true")
        self.assertIn("frame-ancestors 'self' https://preview.example", response.headers["Content-Security-Policy"])
        self.assertNotIn("X-Frame-Options", response.headers)

    def test_deployment_origin_allowlists_reject_wildcards_and_http(self):
        self.assertEqual(
            normalize_origin("HTTPS://Preview.Example:443/", "FRAME_ANCESTORS"),
            "https://preview.example",
        )
        with self.assertRaises(RuntimeError):
            normalize_origin("https://*.example", "FRAME_ANCESTORS")
        with patch("app.APP_ENV", "production"):
            with self.assertRaises(RuntimeError):
                normalize_origin("http://preview.example", "CORS_ALLOWED_ORIGINS")

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

    def test_admin_sos_exposes_and_audits_details_only_after_escalation(self):
        created = self.client.post(
            "/api/sos",
            headers=self.csrf,
            json={"name": "Escalated Caller", "phone": "555-0199", "location": "Private place"},
        )
        request_id = created.get_json()["id"]
        admin_id = self.create_user("ADMIN")
        self.authenticate(admin_id)

        pending = self.client.get("/api/admin/sos").get_json()["requests"]
        pending_row = next(item for item in pending if item["id"] == request_id)
        self.assertNotIn("contact", pending_row)
        self.assertNotIn("location_text", pending_row)

        escalated = self.client.post(f"/api/sos/{request_id}/escalate", headers=self.csrf)
        self.assertEqual(escalated.status_code, 200)
        result = self.client.get("/api/admin/sos").get_json()["requests"]
        escalated_row = next(item for item in result if item["id"] == request_id)
        self.assertEqual(escalated_row["contact"], "555-0199")
        self.assertEqual(escalated_row["location_text"], "Private place")
        with app.app_context():
            audited = get_db().execute(
                """SELECT 1 FROM audit_log
                   WHERE action='sos_details_accessed' AND target_id=? AND actor_id=?""",
                (request_id, admin_id),
            ).fetchone()
        self.assertIsNotNone(audited)

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

    def test_completed_shelter_request_can_be_rated_and_read_back(self):
        ngo_id = self.create_user("NGO")
        shelter_id = self.create_shelter(ngo_id)
        displaced_id = self.create_user("DISPLACED")
        with app.app_context():
            get_db().execute(
                """INSERT INTO help_requests(requester_id,shelter_id,type,status,updated_at,created_at)
                   VALUES(?,?,'shelter','Completed',?,?)""",
                (displaced_id, shelter_id, utcnow(), utcnow()),
            )
            get_db().commit()
        self.authenticate(displaced_id)
        submitted = self.client.post(
            "/api/ratings",
            headers=self.csrf,
            json={"listing_type": "shelter", "listing_id": shelter_id, "stars": 5, "comment": "Helpful staff"},
        )
        self.assertEqual(submitted.status_code, 200)
        rating = self.client.get("/api/ratings/mine").get_json()["ratings"][0]
        self.assertEqual(rating["listing_id"], shelter_id)
        self.assertEqual(rating["stars"], 5)
        self.assertEqual(rating["comment"], "Helpful staff")

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

    def test_ngo_can_create_edit_close_and_reopen_services(self):
        ngo_id = self.create_user("NGO")
        self.authenticate(ngo_id)
        created = self.client.post(
            "/api/services",
            headers=self.csrf,
            json={
                "name": "Community Kitchen",
                "category": "Food",
                "city": "Test City",
                "opening_hours": "10:00-14:00",
                "contact": "555-0166",
            },
        )
        self.assertEqual(created.status_code, 201)
        service_id = created.get_json()["id"]

        admin_id = self.create_user("ADMIN")
        self.authenticate(admin_id)
        approved = self.client.post(
            f"/api/admin/listings/service/{service_id}/approve",
            headers=self.csrf,
        )
        self.assertEqual(approved.status_code, 200)

        self.authenticate(ngo_id)
        updated = self.client.patch(
            f"/api/listings/service/{service_id}",
            headers=self.csrf,
            json={"name": "Updated Kitchen", "category": "Healthcare"},
        )
        self.assertEqual(updated.status_code, 200)
        visible = self.client.get("/api/public/services").get_json()["services"]
        self.assertEqual(next(item for item in visible if item["id"] == service_id)["name"], "Updated Kitchen")

        closed = self.client.post(
            f"/api/listings/service/{service_id}/close",
            headers=self.csrf,
        )
        self.assertEqual(closed.status_code, 200)
        visible_ids = [item["id"] for item in self.client.get("/api/public/services").get_json()["services"]]
        self.assertNotIn(service_id, visible_ids)
        reopened = self.client.post(
            f"/api/listings/service/{service_id}/reopen",
            headers=self.csrf,
        )
        self.assertEqual(reopened.status_code, 200)
        visible_ids = [item["id"] for item in self.client.get("/api/public/services").get_json()["services"]]
        self.assertIn(service_id, visible_ids)

    def test_shelter_owner_can_edit_and_close_public_listing(self):
        ngo_id = self.create_user("NGO")
        shelter_id = self.create_shelter(ngo_id)
        self.authenticate(ngo_id)
        updated = self.client.patch(
            f"/api/listings/shelter/{shelter_id}",
            headers=self.csrf,
            json={"name": "Renamed shelter", "beds_available": 4},
        )
        self.assertEqual(updated.status_code, 200)
        displaced_id = self.create_user("DISPLACED")
        self.authenticate(displaced_id)
        pending = self.client.post(
            "/api/requests",
            headers=self.csrf,
            json={"type": "shelter", "shelter_id": shelter_id},
        )
        self.assertEqual(pending.status_code, 201)
        self.authenticate(ngo_id)
        closed = self.client.post(
            f"/api/listings/shelter/{shelter_id}/close",
            headers=self.csrf,
        )
        self.assertEqual(closed.status_code, 200)
        public_ids = [item["id"] for item in self.client.get("/api/public/shelters").get_json()["shelters"]]
        self.assertNotIn(shelter_id, public_ids)
        blocked_accept = self.client.post(
            f"/api/requests/{pending.get_json()['request']['id']}/accept",
            headers=self.csrf,
        )
        self.assertEqual(blocked_accept.status_code, 409)
        self.authenticate(displaced_id)
        closed_request = self.client.post(
            "/api/requests",
            headers=self.csrf,
            json={"type": "shelter", "shelter_id": shelter_id},
        )
        self.assertEqual(closed_request.status_code, 404)
        self.authenticate(ngo_id)
        reopened = self.client.post(
            f"/api/listings/shelter/{shelter_id}/reopen",
            headers=self.csrf,
        )
        self.assertEqual(reopened.status_code, 200)
        public_shelters = self.client.get("/api/public/shelters").get_json()["shelters"]
        self.assertEqual(next(item for item in public_shelters if item["id"] == shelter_id)["name"], "Renamed shelter")
        other_ngo = self.create_user("NGO")
        self.authenticate(other_ngo)
        forbidden = self.client.patch(
            f"/api/listings/shelter/{shelter_id}",
            headers=self.csrf,
            json={"name": "Not the owner"},
        )
        self.assertEqual(forbidden.status_code, 404)

    def test_alerts_can_be_updated_and_archived(self):
        ngo_id = self.create_user("NGO")
        self.authenticate(ngo_id)
        future_expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        created = self.client.post(
            "/api/alerts",
            headers=self.csrf,
            json={
                "title": "Food distribution",
                "message": "A meal service is open",
                "type": "Food",
                "expires_at": future_expiry,
            },
        )
        self.assertEqual(created.status_code, 201)
        alert_id = created.get_json()["id"]

        updated = self.client.patch(
            f"/api/alerts/{alert_id}",
            headers=self.csrf,
            json={"type": "Medical", "title": "Clinic hours"},
        )
        self.assertEqual(updated.status_code, 200)
        public_alert = next(
            item for item in self.client.get("/api/public/alerts").get_json()["alerts"]
            if item["id"] == alert_id
        )
        self.assertEqual(public_alert["type"], "Medical")
        self.assertEqual(public_alert["title"], "Clinic hours")

        archived = self.client.post(f"/api/alerts/{alert_id}/archive", headers=self.csrf)
        self.assertEqual(archived.status_code, 200)
        public_ids = [item["id"] for item in self.client.get("/api/public/alerts").get_json()["alerts"]]
        self.assertNotIn(alert_id, public_ids)


if __name__ == "__main__":
    unittest.main()
