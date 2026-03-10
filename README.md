FlexDB – SaaS MVP
=================

FlexDB ist eine mehrmandantenfähige SaaS‑Webapp zum Verwalten flexibler Workspaces und Datensätze.
Dieses Repository enthält eine produktionsnahe MVP‑Implementierung mit FastAPI, PostgreSQL,
serverseitig gerendertem HTML (Jinja2 + HTMX) und vorbereiteter Paddle‑Billing‑Integration.

## Features (MVP)

- Benutzerregistrierung, Login, Logout (E‑Mail + Passwort).
- Multi‑Tenant:
  - Jeder Benutzer hat eigene Workspaces und Datensätze.
  - Strikte Trennung der Daten zwischen Benutzern.
- Workspaces:
  - Anlegen/Löschen von Workspaces.
  - Flexible Felder (Workspace‑Felder definieren, um Records zu strukturieren).
  - CRUD von Records.
  - Suche, Filterung, Sortierung (über HTMX‑Teilansichten).
  - Export von Records als CSV.
- Pläne & Feature‑Gating:
  - Free / Plus / Pro Pläne mit Limits (Workspaces, Records, Speicher).
  - Plan‑ und Limitlogik zentral im Plan‑Service.
- Billing (Paddle‑ready):
  - Billing‑Seite mit Upgrade‑Buttons.
  - Webhook‑Endpunkt zur Aktualisierung des lokalen Planstatus.
  - Speicherung von Paddle‑Customer‑ und Subscription‑IDs.
- Storage:
  - Abstrakter Storage‑Service (Dateien/Referenzblätter).
  - Standard: lokales Dateisystem (z.B. Cloud‑Volume).
  - Später leicht erweiterbar auf S3/R2/B2.

## Tech‑Stack

- Python 3.12
- FastAPI
- Uvicorn (ASGI‑Server)
- SQLAlchemy 2.x (Async) + Alembic
- PostgreSQL
- Jinja2 + HTMX + Vanilla JS
- Auth: JWT in HttpOnly‑Cookies, sichere Passwort‑Hashes (bcrypt via passlib)
- Tests: pytest + httpx
- Containerisierung: Docker + docker‑compose

## Projektstruktur

```text
app/
  main.py
  core/
  db/
  models/
  schemas/
  services/
  repositories/
  api/
  web/
  templates/
  static/
  auth/
  billing/
alembic/
tests/
```

## Lokale Entwicklung

### Voraussetzungen

- Python 3.12
- Docker & docker‑compose

### Schritt 1: Environment anlegen

Kopiere `.env.example` nach `.env` und fülle mindestens:

- `DATABASE_URL`
- `SECRET_KEY`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `JWT_REFRESH_TOKEN_EXPIRE_MINUTES`
- `PADDLE_WEBHOOK_SECRET` (Platzhalter ok für lokale Entwicklung)

### Schritt 2: Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### Schritt 3: Datenbank starten (Docker)

```bash
docker-compose up -d db
```

### Schritt 4: Migrationen ausführen

```bash
alembic upgrade head
```

### Schritt 5: App starten

```bash
uvicorn app.main:app --reload
```

Die App ist dann unter `http://127.0.0.1:8000` erreichbar.

## Docker‑Basissetup

Für lokales Testen im Container:

```bash
docker-compose up --build
```

Dies startet:

- den App‑Container (FastAPI + Uvicorn)
- einen PostgreSQL‑Container

## Tests

```bash
pytest
```

## Paddle‑Integration

In dieser MVP‑Version ist Paddle bereits strukturell integriert, aber du musst
deine Live/Test‑Daten selbst hinterlegen:

- `PADDLE_VENDOR_ID`
- `PADDLE_API_KEY`
- `PADDLE_WEBHOOK_SECRET`
- Preis‑IDs/Plan‑IDs (`PADDLE_PLAN_FREE`, `PADDLE_PLAN_PLUS`, `PADDLE_PLAN_PRO` etc.)

**Wichtig:** Paddle authentifiziert NICHT deine App‑User. Die Login-/Session‑Logik
bleibt vollständig in unserer Anwendung. Paddle steuert nur Plan‑ und
Subscription‑Status.

## Storage

Standardmäßig werden hochgeladene Dateien (z.B. Referenzblätter von Kunden)
im lokalen Dateisystem abgelegt. Der Basis‑Pfad wird über `FILE_STORAGE_PATH`
in `.env` konfiguriert.

Für eine spätere Umstellung auf externen Object Storage (S3/R2/B2) ist ein
`StorageService` vorgesehen, der diese Details kapselt.

## carrd.co Landingpage

Die öffentliche Marketing‑Seite (z.B. bei carrd.co) verlinkt auf die App‑URL,
z.B.:

- `https://app.flexdb.ch/login`

Alle Auth‑ und App‑Routen liegen unter der App‑Domain; die Landingpage selbst
bleibt extern gehostet.

