# WarBridge

A responsive React + Vite frontend with a Flask + SQLite backend implementing the WarBridge workflow.

## Run locally

```bash
pnpm install
pnpm dev
```

In a second terminal:

```bash
python -m pip install -r backend_requirements.txt
python app.py
```

Vite proxies `/api` requests to `http://127.0.0.1:5000`. Set a private `SECRET_KEY` before starting the backend.

Create the first administrator account with:

```bash
python create_admin.py
```

The script asks for a username, email, and password and stores only a password hash. Sign-in accepts the NGO or administrator name and password (email can also be used). The selected role must match the database account. An NGO registration option is available from the sign-in form; newly registered NGOs remain read-only until approved by an administrator. Public listings remain empty until partners add real information.

```bash
set SECRET_KEY=replace-with-a-random-secret
python app.py
```

NGO accounts can also be created with `POST /api/auth/register` using role `NGO`; new accounts require administrator verification before write access.

## API areas

- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`
- `GET /api/public/shelters`, `GET /api/public/services`, `GET /api/public/alerts`
- `POST /api/sos`, `POST /api/requests`
- NGO/host request handling, shelter/accommodation creation, verified-partner actions
- Admin verification, report decisions, and audit log

Mutating API requests require the CSRF token from `GET /api/csrf`.

## Safety and implementation boundaries

This implementation is not a production verification system. Before real deployment, complete external identity/document checks, HTTPS deployment, persistent operational logging and backups, native Arabic/Hindi review, and a security review of the deployed environment. An SOS submission is a database request only and does not guarantee a response.

The app cannot determine identity or intent. NGOs, hosts, and shelters must make access decisions and screen people in person. Women-only eligibility is self-declared, not identity verification. Alerts are in-app only, not SMS or push. Listing freshness depends on partner updates. SQLite suits local development; a real deployment should consider PostgreSQL and a documented audit and backup plan.

## Development

The Make environment already manages the preview server.

- `pnpm build` — production frontend build
- `pnpm format` — project formatter

The background image is included at `public/warbridge-camp.png`; the app does not depend on an expiring generated-image URL.
