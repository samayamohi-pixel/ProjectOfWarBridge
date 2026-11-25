import os
import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.getenv("WARBRIDGE_DB", BASE_DIR / "warbridge.db"))

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("HTTPS_ONLY", "0") == "1",
)
if not app.config["SECRET_KEY"]:
    app.config["SECRET_KEY"] = "development-only-change-me"


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('DISPLACED','HOST','NGO','ADMIN')),
            gender TEXT,
            verified INTEGER NOT NULL DEFAULT 0,
            blocked INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS shelters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngo_id INTEGER NOT NULL REFERENCES users(id),
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            area TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            beds_available INTEGER NOT NULL DEFAULT 0,
            women_safe INTEGER NOT NULL DEFAULT 0,
            family_friendly INTEGER NOT NULL DEFAULT 0,
            verified INTEGER NOT NULL DEFAULT 0,
            blocked INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS help_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_id INTEGER REFERENCES users(id),
            handler_id INTEGER REFERENCES users(id),
            shelter_id INTEGER REFERENCES shelters(id),
            accommodation_id INTEGER REFERENCES accommodations(id),
            type TEXT NOT NULL,
            message TEXT,
            contact TEXT,
            location_text TEXT,
            status TEXT NOT NULL DEFAULT 'Pending',
            is_sos INTEGER NOT NULL DEFAULT 0,
            handled_by INTEGER REFERENCES users(id),
            updated_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS accommodations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_id INTEGER NOT NULL REFERENCES users(id),
            city TEXT NOT NULL,
            area TEXT NOT NULL,
            address TEXT,
            rooms INTEGER NOT NULL,
            women_only INTEGER NOT NULL DEFAULT 0,
            description TEXT,
            verified INTEGER NOT NULL DEFAULT 0,
            blocked INTEGER NOT NULL DEFAULT 0,
            closed INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id INTEGER NOT NULL REFERENCES users(id),
            listing_type TEXT NOT NULL,
            listing_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            admin_id INTEGER REFERENCES users(id),
            updated_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(reporter_id, listing_type, listing_id)
        );
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            listing_type TEXT NOT NULL,
            listing_id INTEGER NOT NULL,
            stars INTEGER NOT NULL CHECK(stars BETWEEN 1 AND 5),
            comment TEXT,
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, listing_type, listing_id)
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngo_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL,
            expires_at TEXT,
            blocked INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngo_id INTEGER NOT NULL REFERENCES users(id),
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            city TEXT NOT NULL,
            opening_hours TEXT,
            contact TEXT,
            address TEXT,
            verified INTEGER NOT NULL DEFAULT 0,
            blocked INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_id INTEGER REFERENCES users(id),
            action TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            detail TEXT,
            created_at TEXT NOT NULL
        );
        """
    )
    db.commit()

    admin_email = os.getenv("WARBRIDGE_ADMIN_EMAIL")
    admin_password = os.getenv("WARBRIDGE_ADMIN_PASSWORD")
    if admin_email and admin_password:
        existing = db.execute("SELECT id FROM users WHERE email = ?", (admin_email.lower(),)).fetchone()
        if not existing:
            db.execute(
                "INSERT INTO users(name,email,password_hash,role,verified,created_at) VALUES(?,?,?,?,1,?)",
                ("Administrator", admin_email.lower(), generate_password_hash(admin_password), "ADMIN", utcnow()),
            )
            db.commit()


@app.before_request
def setup():
    init_db()
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)


def require_csrf():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        supplied = request.headers.get("X-CSRF-Token") or (request.get_json(silent=True) or {}).get("_csrf")
        if not supplied or not secrets.compare_digest(supplied, session.get("csrf_token", "")):
            return jsonify({"error": "Invalid CSRF token"}), 403
    return None


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()


def role_required(*roles):
    def decorator(fn):
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            if user["blocked"]:
                return jsonify({"error": "Account blocked"}), 403
            if user["role"] not in roles:
                return jsonify({"error": "Forbidden"}), 403
            return fn(user, *args, **kwargs)
        wrapped.__name__ = fn.__name__
        return wrapped
    return decorator


def verified_required(user):
    return user["role"] == "ADMIN" or bool(user["verified"])


def audit(actor_id, action, target_type=None, target_id=None, detail=None):
    get_db().execute(
        "INSERT INTO audit_log(actor_id,action,target_type,target_id,detail,created_at) VALUES(?,?,?,?,?,?)",
        (actor_id, action, target_type, target_id, detail, utcnow()),
    )
    get_db().commit()


def json_row(row):
    return dict(row) if row else None


def public_user(user):
    if not user:
        return None
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "gender": user["gender"],
        "verified": bool(user["verified"]),
    }


@app.get("/api/csrf")
def csrf():
    return jsonify({"csrfToken": session["csrf_token"]})


@app.post("/api/auth/register")
def register():
    denied = require_csrf()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    role = str(data.get("role", "")).upper()
    gender = str(data.get("gender", "")).strip() or None
    if not name or not email or len(password) < 8:
        return jsonify({"error": "Name, email and a password of at least 8 characters are required"}), 400
    if role not in ("DISPLACED", "HOST", "NGO"):
        return jsonify({"error": "Role must be Displaced, Host or NGO"}), 400
    db = get_db()
    if db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
        return jsonify({"error": "An account already exists for this email"}), 409
    if role in ("HOST", "NGO") and db.execute(
        "SELECT id FROM users WHERE role=? AND LOWER(name)=LOWER(?)",
        (role, name),
    ).fetchone():
        return jsonify({"error": "An account already exists for this partner name"}), 409
    cur = db.execute(
        "INSERT INTO users(name,email,password_hash,role,gender,verified,blocked,created_at) VALUES(?,?,?,?,?,?,0,?)",
        (name, email, generate_password_hash(password), role, gender, 0, utcnow()),
    )
    db.commit()
    session.clear()
    session["user_id"] = cur.lastrowid
    session["csrf_token"] = secrets.token_urlsafe(32)
    user = db.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify({"user": public_user(user), "csrfToken": session["csrf_token"]})


LOGIN_ATTEMPTS = {}


@app.post("/api/auth/login")
def login():
    denied = require_csrf()
    if denied:
        return denied
    ip = request.remote_addr or "unknown"
    now = time.time()
    record = LOGIN_ATTEMPTS.setdefault(ip, [])
    record[:] = [timestamp for timestamp in record if now - timestamp < 300]
    if len(record) >= 5:
        return jsonify({"error": "Too many login attempts. Try again later."}), 429
    data = request.get_json(silent=True) or {}
    identity = str(data.get("identity", "")).strip().lower()
    role = str(data.get("role", "")).strip().upper()
    password = str(data.get("password", ""))
    if role not in ("NGO", "ADMIN"):
        return jsonify({"error": "Choose NGO or Administrator sign-in"}), 400
    if not identity or not password:
        return jsonify({"error": "Name and password are required"}), 400
    users = get_db().execute(
        """SELECT * FROM users
           WHERE role=? AND (LOWER(name)=? OR LOWER(email)=?)""",
        (role, identity, identity),
    ).fetchall()
    matches = [user for user in users if check_password_hash(user["password_hash"], password)]
    if len(matches) > 1:
        return jsonify({"error": "This name matches multiple accounts. Sign in with the account email instead."}), 409
    if not matches:
        record.append(now)
        return jsonify({"error": "Invalid name or password"}), 401
    user = matches[0]
    record.clear()
    if user["blocked"]:
        return jsonify({"error": "Account blocked"}), 403
    session.clear()
    session["user_id"] = user["id"]
    session["csrf_token"] = secrets.token_urlsafe(32)
    return jsonify({"user": public_user(user), "csrfToken": session["csrf_token"]})


@app.post("/api/auth/logout")
def logout():
    denied = require_csrf()
    if denied:
        return denied
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/auth/me")
def me():
    user = current_user()
    return jsonify({"user": public_user(user)})


@app.get("/api/public/alerts")
def public_alerts():
    now = utcnow()
    rows = get_db().execute(
        """SELECT a.*, u.name AS partner_name FROM alerts a
           JOIN users u ON u.id=a.ngo_id
           WHERE a.blocked=0 AND (a.expires_at IS NULL OR a.expires_at > ?)
           ORDER BY a.created_at DESC LIMIT 3""",
        (now,),
    ).fetchall()
    return jsonify({"alerts": [json_row(row) for row in rows]})


@app.get("/api/public/shelters")
def public_shelters():
    city = request.args.get("city", "").strip()
    women_safe = request.args.get("women_safe") == "1"
    family_friendly = request.args.get("family_friendly") == "1"
    where = ["s.blocked=0", "s.verified=1"]
    params = []
    if city:
        where.append("LOWER(s.city) LIKE LOWER(?)")
        params.append(f"%{city}%")
    if women_safe:
        where.append("s.women_safe=1")
    if family_friendly:
        where.append("s.family_friendly=1")
    rows = get_db().execute(
        f"""SELECT s.id,s.name,s.city,s.area,s.beds_available,s.women_safe,
                   s.family_friendly,s.verified,s.updated_at,
                   COALESCE(ROUND(AVG(r.stars),1),0) AS rating,
                   COUNT(r.id) AS rating_count
            FROM shelters s LEFT JOIN ratings r ON r.listing_type='shelter' AND r.listing_id=s.id
            WHERE {' AND '.join(where)}
            GROUP BY s.id ORDER BY s.verified DESC,s.beds_available DESC,s.updated_at DESC""",
        params,
    ).fetchall()
    return jsonify({"shelters": [json_row(row) for row in rows]})


@app.get("/api/public/services")
def public_services():
    city = request.args.get("city", "").strip()
    category = request.args.get("category", "").strip()
    where = ["blocked=0", "verified=1"]
    params = []
    if city:
        where.append("LOWER(city) LIKE LOWER(?)")
        params.append(f"%{city}%")
    if category:
        where.append("LOWER(category)=LOWER(?)")
        params.append(category)
    rows = get_db().execute(
        f"SELECT id,name,category,city,opening_hours,contact,updated_at FROM services WHERE {' AND '.join(where)} ORDER BY updated_at DESC",
        params,
    ).fetchall()
    return jsonify({"services": [json_row(row) for row in rows]})


@app.post("/api/sos")
def create_sos():
    denied = require_csrf()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    if data.get("website"):
        return jsonify({"ok": True})
    ip = request.remote_addr or "unknown"
    key = ("sos", ip)
    record = LOGIN_ATTEMPTS.setdefault(key, [])
    now = time.time()
    record[:] = [timestamp for timestamp in record if now - timestamp < 300]
    if len(record) >= 3:
        return jsonify({"error": "Too many SOS submissions. Please call 112 if this is an emergency."}), 429
    record.append(now)
    db = get_db()
    cur = db.execute(
        """INSERT INTO help_requests(requester_id,type,message,contact,location_text,status,is_sos,updated_at,created_at)
           VALUES(NULL,'SOS',?,?,?, 'Pending',1,?,?)""",
        (str(data.get("message", ""))[:1000], str(data.get("phone", ""))[:40], str(data.get("location", ""))[:300], utcnow(), utcnow()),
    )
    db.commit()
    audit(current_user()["id"] if current_user() else None, "sos_created", "help_request", cur.lastrowid)
    return jsonify({"ok": True, "id": cur.lastrowid})


@app.post("/api/requests")
@role_required("DISPLACED")
def create_request(user):
    denied = require_csrf()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    request_type = str(data.get("type", "shelter")).strip().lower()
    shelter_id = data.get("shelter_id")
    accommodation_id = data.get("accommodation_id")
    if not shelter_id and not accommodation_id:
        return jsonify({"error": "A shelter or accommodation is required"}), 400
    db = get_db()
    if shelter_id:
        shelter = db.execute("SELECT * FROM shelters WHERE id=?", (shelter_id,)).fetchone()
        if not shelter or shelter["blocked"] or not shelter["verified"]:
            return jsonify({"error": "Shelter is not available"}), 404
        if shelter["women_safe"] and str(user["gender"]).lower() != "female":
            return jsonify({"error": "This listing is restricted to users who identified as female"}), 403
        duplicate = db.execute(
            "SELECT id FROM help_requests WHERE requester_id=? AND shelter_id=? AND status IN ('Pending','Accepted')",
            (user["id"], shelter_id),
        ).fetchone()
    else:
        accommodation = db.execute("SELECT * FROM accommodations WHERE id=?", (accommodation_id,)).fetchone()
        if not accommodation or accommodation["blocked"] or not accommodation["verified"]:
            return jsonify({"error": "Accommodation is not available"}), 404
        if accommodation["women_only"] and str(user["gender"]).lower() != "female":
            return jsonify({"error": "This listing is restricted to users who identified as female"}), 403
        duplicate = db.execute(
            "SELECT id FROM help_requests WHERE requester_id=? AND accommodation_id=? AND status IN ('Pending','Accepted')",
            (user["id"], accommodation_id),
        ).fetchone()
    if duplicate:
        return jsonify({"error": "An active request already exists"}), 409
    cur = db.execute(
        """INSERT INTO help_requests(requester_id,type,message,contact,shelter_id,accommodation_id,status,updated_at,created_at)
           VALUES(?,?,?,?,?,?, 'Pending', ?, ?)""",
        (user["id"], request_type, str(data.get("message", ""))[:1000],
         str(data.get("contact", ""))[:40], shelter_id, accommodation_id, utcnow(), utcnow()),
    )
    db.commit()
    audit(user["id"], "request_created", "help_request", cur.lastrowid)
    return jsonify({"request": {"id": cur.lastrowid, "status": "Pending"}}), 201


@app.get("/api/requests/mine")
@role_required("DISPLACED")
def mine_requests(user):
    rows = get_db().execute(
        """SELECT r.*, s.name AS shelter_name, s.address AS shelter_address,
                  s.phone AS shelter_phone, s.area AS shelter_area,
                  a.address AS accommodation_address
           FROM help_requests r
           LEFT JOIN shelters s ON s.id=r.shelter_id
           LEFT JOIN accommodations a ON a.id=r.accommodation_id
           WHERE r.requester_id=? ORDER BY r.created_at DESC""",
        (user["id"],),
    ).fetchall()
    result = []
    for row in rows:
        item = json_row(row)
        if item["status"] != "Accepted":
            item.pop("shelter_address", None)
            item.pop("shelter_phone", None)
            item.pop("accommodation_address", None)
        result.append(item)
    return jsonify({"requests": result})


@app.post("/api/requests/<int:request_id>/cancel")
@role_required("DISPLACED")
def cancel_request(user, request_id):
    denied = require_csrf()
    if denied:
        return denied
    db = get_db()
    row = db.execute("SELECT * FROM help_requests WHERE id=?", (request_id,)).fetchone()
    if not row or row["requester_id"] != user["id"]:
        return jsonify({"error": "Request not found"}), 404
    if row["status"] not in ("Pending", "Accepted"):
        return jsonify({"error": "Request cannot be cancelled"}), 409
    db.execute("UPDATE help_requests SET status='Cancelled',handled_by=?,updated_at=? WHERE id=?",
               (user["id"], utcnow(), request_id))
    restore_request_bed(db, row)
    db.commit()
    audit(user["id"], "request_cancelled", "help_request", request_id)
    return jsonify({"ok": True})


@app.get("/api/requests/incoming")
@role_required("NGO", "HOST")
def incoming_requests(user):
    db = get_db()
    if user["role"] == "NGO":
        rows = db.execute(
            """SELECT r.* FROM help_requests r JOIN shelters s ON s.id=r.shelter_id
               WHERE s.ngo_id=? AND r.status IN ('Pending','Accepted') ORDER BY r.is_sos DESC,r.created_at ASC""",
            (user["id"],),
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT r.* FROM help_requests r JOIN accommodations a ON a.id=r.accommodation_id
               WHERE a.host_id=? AND r.status IN ('Pending','Accepted') ORDER BY r.created_at ASC""",
            (user["id"],),
        ).fetchall()
    return jsonify({"requests": [json_row(row) for row in rows]})


def restore_request_bed(db, row):
    if row["status"] == "Accepted" and row["shelter_id"]:
        db.execute("UPDATE shelters SET beds_available=beds_available+1,updated_at=? WHERE id=?",
                   (utcnow(), row["shelter_id"]))


@app.post("/api/requests/<int:request_id>/<action>")
@role_required("NGO", "HOST")
def handle_request(user, request_id, action):
    denied = require_csrf()
    if denied:
        return denied
    if not verified_required(user):
        return jsonify({"error": "Verification required"}), 403
    if action not in ("accept", "reject", "complete"):
        return jsonify({"error": "Invalid action"}), 404
    db = get_db()
    row = db.execute("SELECT * FROM help_requests WHERE id=?", (request_id,)).fetchone()
    if not row:
        return jsonify({"error": "Request not found"}), 404
    if user["role"] == "NGO" and row["shelter_id"]:
        owned = db.execute("SELECT 1 FROM shelters WHERE id=? AND ngo_id=?", (row["shelter_id"], user["id"])).fetchone()
        if not owned:
            return jsonify({"error": "Forbidden"}), 403
    if user["role"] == "HOST" and row["accommodation_id"]:
        owned = db.execute("SELECT 1 FROM accommodations WHERE id=? AND host_id=?", (row["accommodation_id"], user["id"])).fetchone()
        if not owned:
            return jsonify({"error": "Forbidden"}), 403
    valid = (
        action == "accept" and row["status"] == "Pending"
        or action == "reject" and row["status"] == "Pending"
        or action == "complete" and row["status"] == "Accepted"
    )
    if not valid:
        return jsonify({"error": "Invalid status transition"}), 409
    if action == "accept" and row["shelter_id"]:
        shelter = db.execute("SELECT beds_available FROM shelters WHERE id=?", (row["shelter_id"],)).fetchone()
        if not shelter or shelter["beds_available"] < 1:
            return jsonify({"error": "No beds available"}), 409
        db.execute("UPDATE shelters SET beds_available=beds_available-1,updated_at=? WHERE id=?",
                   (utcnow(), row["shelter_id"]))
    status = {"accept": "Accepted", "reject": "Rejected", "complete": "Completed"}[action]
    db.execute("UPDATE help_requests SET status=?,handled_by=?,updated_at=? WHERE id=?",
               (status, user["id"], utcnow(), request_id))
    if action == "complete":
        restore_request_bed(db, dict(row))
    db.commit()
    audit(user["id"], f"request_{action}", "help_request", request_id)
    return jsonify({"ok": True, "status": status})


@app.post("/api/shelters")
@role_required("NGO")
def create_shelter(user):
    denied = require_csrf()
    if denied:
        return denied
    if not verified_required(user):
        return jsonify({"error": "NGO verification required"}), 403
    data = request.get_json(silent=True) or {}
    name, city, area = str(data.get("name", "")).strip(), str(data.get("city", "")).strip(), str(data.get("area", "")).strip()
    try:
        beds = int(data.get("beds_available", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "beds_available must be a number"}), 400
    if not name or not city or not area or beds < 0:
        return jsonify({"error": "Name, city, area and non-negative bed count are required"}), 400
    db = get_db()
    cur = db.execute(
        """INSERT INTO shelters(ngo_id,name,city,area,address,phone,beds_available,women_safe,family_friendly,verified,blocked,updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,1,0,?)""",
        (user["id"], name, city, area, str(data.get("address", ""))[:300],
         str(data.get("phone", ""))[:40], beds, int(bool(data.get("women_safe"))),
         int(bool(data.get("family_friendly"))), utcnow()),
    )
    db.commit()
    audit(user["id"], "shelter_created", "shelter", cur.lastrowid)
    return jsonify({"id": cur.lastrowid}), 201


@app.post("/api/accommodations")
@role_required("HOST")
def create_accommodation(user):
    denied = require_csrf()
    if denied:
        return denied
    if not verified_required(user):
        return jsonify({"error": "Host verification required"}), 403
    data = request.get_json(silent=True) or {}
    city, area = str(data.get("city", "")).strip(), str(data.get("area", "")).strip()
    try:
        rooms = int(data.get("rooms", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "rooms must be a number"}), 400
    if not city or not area or rooms < 1:
        return jsonify({"error": "City, area and at least one room are required"}), 400
    cur = get_db().execute(
        """INSERT INTO accommodations(host_id,city,area,address,rooms,women_only,description,verified,blocked,closed,updated_at)
           VALUES(?,?,?,?,?,?,?,1,0,0,?)""",
        (user["id"], city, area, str(data.get("address", ""))[:300], rooms,
         int(bool(data.get("women_only"))), str(data.get("description", ""))[:1000], utcnow()),
    )
    get_db().commit()
    audit(user["id"], "accommodation_created", "accommodation", cur.lastrowid)
    return jsonify({"id": cur.lastrowid}), 201


@app.post("/api/alerts")
@role_required("NGO", "ADMIN")
def create_alert(user):
    denied = require_csrf()
    if denied:
        return denied
    if user["role"] == "NGO" and not verified_required(user):
        return jsonify({"error": "NGO verification required"}), 403
    data = request.get_json(silent=True) or {}
    title, message = str(data.get("title", "")).strip(), str(data.get("message", "")).strip()
    alert_type = str(data.get("type", "Warning")).strip()
    if not title or not message or alert_type not in ("Food", "Shelter", "Medical", "Warning"):
        return jsonify({"error": "Title, message and a valid alert type are required"}), 400
    expires_at = data.get("expires_at")
    cur = get_db().execute(
        "INSERT INTO alerts(ngo_id,title,message,type,expires_at,blocked,updated_at,created_at) VALUES(?,?,?,?,?,0,?,?)",
        (user["id"], title[:200], message[:2000], alert_type, expires_at, utcnow(), utcnow()),
    )
    get_db().commit()
    audit(user["id"], "alert_created", "alert", cur.lastrowid)
    return jsonify({"id": cur.lastrowid}), 201


@app.post("/api/reports")
@role_required("DISPLACED", "HOST", "NGO", "ADMIN")
def create_report(user):
    denied = require_csrf()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    listing_type = str(data.get("listing_type", "")).strip()
    listing_id = data.get("listing_id")
    reason = str(data.get("reason", "")).strip()
    if listing_type not in ("shelter", "accommodation", "service") or not isinstance(listing_id, int):
        return jsonify({"error": "Valid listing_type and listing_id are required"}), 400
    if len(reason) < 5:
        return jsonify({"error": "Reason must be at least 5 characters"}), 400
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO reports(reporter_id,listing_type,listing_id,reason,status,updated_at,created_at) VALUES(?,?,?,?, 'Open', ?, ?)",
            (user["id"], listing_type, listing_id, reason[:1000], utcnow(), utcnow()),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "You have already reported this listing"}), 409
    audit(user["id"], "listing_reported", listing_type, listing_id)
    return jsonify({"id": cur.lastrowid}), 201


@app.post("/api/ratings")
@role_required("DISPLACED")
def create_rating(user):
    denied = require_csrf()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    listing_type = str(data.get("listing_type", "")).strip()
    listing_id = data.get("listing_id")
    try:
        stars = int(data.get("stars", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "stars must be a number"}), 400
    if listing_type not in ("shelter", "accommodation", "service") or not isinstance(listing_id, int) or not 1 <= stars <= 5:
        return jsonify({"error": "Valid listing and 1 to 5 stars are required"}), 400
    db = get_db()
    if listing_type == "shelter":
        completed = db.execute(
            "SELECT id FROM help_requests WHERE requester_id=? AND shelter_id=? AND status='Completed'",
            (user["id"], listing_id),
        ).fetchone()
    elif listing_type == "accommodation":
        completed = db.execute(
            "SELECT id FROM help_requests WHERE requester_id=? AND accommodation_id=? AND status='Completed'",
            (user["id"], listing_id),
        ).fetchone()
    else:
        completed = True
    if not completed:
        return jsonify({"error": "Ratings require a completed request"}), 403
    db.execute(
        """INSERT INTO ratings(user_id,listing_type,listing_id,stars,comment,updated_at)
           VALUES(?,?,?,?,?,?)
           ON CONFLICT(user_id,listing_type,listing_id) DO UPDATE SET stars=excluded.stars,comment=excluded.comment,updated_at=excluded.updated_at""",
        (user["id"], listing_type, listing_id, stars, str(data.get("comment", ""))[:1000], utcnow()),
    )
    db.commit()
    audit(user["id"], "rating_submitted", listing_type, listing_id)
    return jsonify({"ok": True})


@app.get("/api/admin/verifications")
@role_required("ADMIN")
def admin_verifications(user):
    rows = get_db().execute(
        "SELECT id,name,email,role,verified,created_at FROM users WHERE role IN ('HOST','NGO') AND verified=0 AND blocked=0 ORDER BY created_at DESC"
    ).fetchall()
    return jsonify({"users": [json_row(row) for row in rows]})


@app.post("/api/admin/users/<int:user_id>/verify")
@role_required("ADMIN")
def verify_user(user, user_id):
    denied = require_csrf()
    if denied:
        return denied
    db = get_db()
    target = db.execute("SELECT * FROM users WHERE id=? AND role IN ('HOST','NGO')", (user_id,)).fetchone()
    if not target:
        return jsonify({"error": "Partner not found"}), 404
    db.execute("UPDATE users SET verified=1 WHERE id=?", (user_id,))
    db.commit()
    audit(user["id"], "partner_verified", "user", user_id)
    return jsonify({"ok": True})


@app.post("/api/admin/users/<int:user_id>/reject")
@role_required("ADMIN")
def reject_user(user, user_id):
    denied = require_csrf()
    if denied:
        return denied
    db = get_db()
    target = db.execute(
        "SELECT id FROM users WHERE id=? AND role IN ('HOST','NGO') AND verified=0",
        (user_id,),
    ).fetchone()
    if not target:
        return jsonify({"error": "Pending partner not found"}), 404
    db.execute("UPDATE users SET blocked=1 WHERE id=?", (user_id,))
    db.commit()
    audit(user["id"], "partner_rejected", "user", user_id)
    return jsonify({"ok": True})


@app.post("/api/admin/reports/<int:report_id>/<action>")
@role_required("ADMIN")
def handle_report(user, report_id, action):
    denied = require_csrf()
    if denied:
        return denied
    if action not in ("block", "dismiss", "unblock"):
        return jsonify({"error": "Invalid action"}), 404
    db = get_db()
    report = db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    if not report:
        return jsonify({"error": "Report not found"}), 404
    table = {"shelter": "shelters", "accommodation": "accommodations", "service": "services"}[report["listing_type"]]
    if action in ("block", "unblock"):
        db.execute(f"UPDATE {table} SET blocked=? WHERE id=?", (1 if action == "block" else 0, report["listing_id"]))
        if action == "block":
            db.execute("UPDATE reports SET status='Closed',admin_id=?,updated_at=? WHERE listing_type=? AND listing_id=?",
                       (user["id"], utcnow(), report["listing_type"], report["listing_id"]))
    else:
        db.execute("UPDATE reports SET status='Dismissed',admin_id=?,updated_at=? WHERE id=?",
                   (user["id"], utcnow(), report_id))
    db.commit()
    audit(user["id"], f"listing_{action}", report["listing_type"], report["listing_id"])
    return jsonify({"ok": True})


@app.get("/api/admin/audit")
@role_required("ADMIN")
def audit_log(user):
    rows = get_db().execute("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 200").fetchall()
    return jsonify({"audit": [json_row(row) for row in rows]})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
