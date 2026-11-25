# WarBridge

A responsive React + Vite frontend with a Flask + SQLite backend implementing the WarBridge workflow.

## Run locally

```bash
pnpm install
pnpm dev
```

In a second terminal, set explicit development configuration and start the backend:

```powershell
$env:WARBRIDGE_ENV = "development"
$env:SECRET_KEY = "local-development-only-change-this"
python -m pip install -r backend_requirements.txt
python app.py
```

Vite proxies `/api` requests to `http://127.0.0.1:5000`. The known fallback key is available only in explicit development mode. Never use it in a deployment.

Create the first administrator account with:

```bash
python create_admin.py
```

The script asks for a username, email, and password and stores only a password hash. Set the same environment variables before running it.

Displaced people, hosts, and NGOs can register through the sign-in form. Host and NGO accounts require administrator verification. New shelters and accommodations also require separate administrator listing approval before they appear publicly.

## API areas

- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`
- `GET /api/public/shelters`, `GET /api/public/accommodations`, `GET /api/public/services`, `GET /api/public/alerts`
- `POST /api/sos`, `POST /api/requests`
- Verified NGO SOS queue: `GET /api/sos/incoming`, `POST /api/sos/<id>/claim`, `POST /api/sos/<id>/escalate`, `POST /api/sos/<id>/resolve`
- NGO/host request handling, shelter/accommodation creation, verified-partner actions
- Admin verification, listing moderation, reports, SOS monitoring, and audit log
- Health checks: `GET /api/health/live`, `GET /api/health/ready`

Mutating API requests require the CSRF token from `GET /api/csrf`.

## Production

Production startup requires a private `SECRET_KEY` of at least 32 characters and `HTTPS_ONLY=1`. Session cookies are secure outside development/test. Run behind HTTPS termination with Gunicorn; do not use `python app.py` in production. If a trusted reverse proxy forwards client IP headers, set `TRUSTED_PROXY_COUNT` to the exact number of trusted proxy hops; forwarded headers are not trusted by default.

```bash
WARBRIDGE_ENV=production SECRET_KEY="<private-random-value>" HTTPS_ONLY=1 gunicorn --workers 2 --bind 127.0.0.1:5000 app:app
```

SQLite is intended for local development and small pilots. The app applies versioned schema migrations on startup and uses database-backed rate limits and atomic capacity transactions. Production still requires a shared production database, encrypted backups and restore tests, monitoring, and locally reviewed emergency escalation procedures.

## Safety and implementation boundaries

An SOS is stored in a private database queue; it is not sent to emergency services, and no response is guaranteed. A verified NGO must explicitly claim it before contact/location details are released. Escalation changes its state and exposes it to administrators; it does not dispatch an external alert.

The app cannot determine identity or intent. NGOs, hosts, and shelters must make access decisions and screen people in person. Women-only eligibility is self-declared, not identity verification. Alerts are in-app only, not SMS or push. Listing freshness depends on partner updates. Complete external identity/document checks, persistent operational logging and backups, native Arabic/Hindi review, and a security and safeguarding review before real deployment.

## Development

The Make environment already manages the preview server.

- `pnpm build` — production frontend build
- `pnpm format` — project formatter
- `python -m unittest discover -s tests -v` — backend regression tests

The background image is included at `public/warbridge-camp.png`; the app does not depend on an expiring generated-image URL.
