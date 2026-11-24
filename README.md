# WarBridge — visual prototype

A responsive React + Vite recreation of the supplied four-panel WarBridge reference, with a locally stored, generated night-camp background and violet, green, red, and blue role themes.

## Preview interactions

- Browse and filter example shelters and explore services and emergency helplines.
- Add demo shelter requests and cancel them.
- Accept sample requests in the NGO panel.
- Publish session-only alerts and view them through the public Alerts dialog.
- Review and approve or reject sample partners; block or dismiss a sample report.
- Explore demo SOS, reporting, and completed-stay rating dialogs.

All examples are fictional. Changes live in React memory and reset on reload. The top navigation switches between a full-size Find Help cover and My Support (displaced user), Partner Hub (NGO), and Trust & Safety (admin) pages. They are demo views, not authenticated or access-controlled pages.

## Safety and implementation boundaries

This is **not** the Flask + SQLite production system described in the workflow specification. There is no backend, real authentication, database, permanent audit history, document verification, message delivery, or actual NGO routing. Demo SOS submissions do not alert anyone. For immediate assistance in India, call **112**, **181** (women's helpline), or **1098** (child helpline).

Production work must implement server-enforced authorization and ownership, administrator-controlled verification, CSRF protection, password hashing, secure cookies and secrets, rate limiting, private address/contact release, transactional capacity management, valid request transitions, reporting and rating constraints, alert expiry, and durable audit records before this can safely handle real people or data.

The app cannot determine identity or intent. NGOs, hosts, and shelters must make access decisions and screen people in person. Women-only eligibility is self-declared, not identity verification. Alerts are in-app only, not SMS or push. Listing freshness depends on partner updates. SQLite suits a demo or pilot; deployment requires a backup and audit plan and consideration of PostgreSQL. Arabic and Hindi translations require native review; this prototype is English-only.

## Development

The Make environment already manages the preview server.

- `pnpm build` — production frontend build
- `pnpm format` — project formatter

The background image is included at `public/warbridge-camp.png`; the app does not depend on an expiring generated-image URL.
