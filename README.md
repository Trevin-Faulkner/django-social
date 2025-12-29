# ConnectPro (Django + Tailwind)

Modern, anti-corporate networking space for entrepreneurs with role-based discovery, connection limits, and lightweight real-time chat.

## Tech
- Django 5.2.6, Python 3.13
- Templates + Tailwind CDN (Space Grotesk)
- PostgreSQL (env-driven) with SQLite fallback for local dev
- PayPal checkout stub (plan upgrade endpoint) + Google OAuth placeholder hook
  - Now wired to django-allauth Google provider (`/accounts/google/login/`)

## Running locally
1) Create env (optional) and install deps:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
2) Configure DB via env (example):
```bash
export POSTGRES_DB=connectpro
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
```
Without env it will use `db.sqlite3` for convenience.

3) Apply migrations:
```bash
python3 manage.py migrate
```

4) Seed demo data (creates sample users, experience, chat threads):
```bash
python3 manage.py seed_demo
```
Demo login: `sarah/password123` (developer) and `alex/password123` (client). Others: `maria`, `james`, `emily` with the same password.

5) Run the server:
```bash
python3 manage.py runserver
```

## Features
- **Auth**: Email/username + password with Google button stub (`/google-login/`), custom signup form with role pick (Client or Developer).
- **Profiles**: Headline, bio, skills, goals, location, plan badge, experience history, profile views metric, inline edit form for your own profile.
- **Roles & Discovery**: Users only see the opposite role in Discover; search by name/skills/location; cards match the provided UI.
- **Connections & Limits**: Plans enforce daily connection caps — Free: 2/day, Plus: 5/day, Pro: unlimited. Remaining/active counts shown on Profile & Discover banners.
- **Messaging**: Conversations auto-created on connect; two-way chat with polling every 4s (`/api/messages/<id>/` endpoints) and inline send form.
- **Plans & Payments**: Upgrade buttons hit `/upgrade/<plan>/` which updates the membership plan and mimics PayPal success; ready to replace with real PayPal SDK.
  - One-time PayPal payments via `paypalrestsdk`: set `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_ENV=sandbox|live`; upgrade buttons create a PayPal payment and redirect for approval, then execute and upgrade the plan.
- **UI**: Tailwind-based replicas of the provided screenshots (landing, pricing, auth, discover, profile, messages).

## Notes
- Set `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS` in production; `DEBUG` is driven by `DJANGO_DEBUG` (default `true`).
- Static assets served from `/static`; Tailwind is pulled from CDN so no build step is required.

## Google login (django-allauth)
1) Install requirements if not yet: `pip install -r requirements.txt`
2) In Django admin, add a `Site` with domain `localhost:8000` and set `SITE_ID` env if you create a different ID.
3) Create a Google OAuth client (Web) and add the redirect URI: `http://localhost:8000/accounts/google/login/callback/`
4) In Django admin → Social Accounts → Social applications, add Google with the client ID/secret and attach the Site.
5) Alternatively export env vars `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` and restart; the provider config will pick them up.
6) The "Continue with Google" buttons now point to `/accounts/google/login/` (allauth).
