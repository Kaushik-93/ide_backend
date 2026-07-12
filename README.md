# Intelligent Document Engine — FastAPI + Postgres

CRUD API over the schema you already created locally (`schema.sql`).

## 1. Install dependencies

```bash
cd docengine_api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure the database connection

```bash
cp .env.example .env
```

Edit `.env` and set your Mac username (run `whoami` if unsure):
```
DATABASE_URL=postgresql+psycopg2://YOUR_MAC_USERNAME@localhost:5432/docengine
```

## 3. Run the API

```bash
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000/docs** — interactive Swagger UI with every
endpoint, where you can try requests directly in the browser.

## What's included

Standard CRUD (`POST` / `GET` list / `GET` one / `PATCH` / `DELETE`) for:
`organizations`, `users`, `org-memberships`, `invitations`, `documents`,
`document-permissions`, `document-nodes`, `node-embeddings`,
`processing-jobs`, `credit-pricing`.

Restricted endpoints (by design, matching schema.sql's rules):
- **`audit-logs`** — create + read only. No update/delete: audit logs are
  append-only.
- **`wallets`** — create (to provision a new wallet) + read only.
  Balance is never edited directly here.
- **`credit-holds`** / **`credit-transactions`** — read only. These are
  the ledger; they're written exclusively by the functions below.
- **`/credits/topup`**, **`/credits/reserve`**, **`/credits/capture/{hold_id}`**,
  **`/credits/release/{hold_id}`** — call the Postgres functions
  (`fn_add_credits`, `fn_reserve_credits`, `fn_capture_hold`,
  `fn_release_hold`) directly, so wallet balances and the ledger can
  never drift apart, even under concurrent requests.

## Try it: quick end-to-end example

```bash
# 1. Create an org
curl -X POST localhost:8000/organizations/ -H "Content-Type: application/json" \
  -d '{"name": "Acme Inc", "slug": "acme"}'

# 2. Create a user
curl -X POST localhost:8000/users/ -H "Content-Type: application/json" \
  -d '{"email": "you@acme.com", "full_name": "You"}'

# 3. Provision a wallet for that org
curl -X POST localhost:8000/wallets/ -H "Content-Type: application/json" \
  -d '{"owner_type": "organization", "owner_id": "<org_id_from_step_1>"}'

# 4. Top it up
curl -X POST localhost:8000/credits/topup -H "Content-Type: application/json" \
  -d '{"wallet_id": "<wallet_id_from_step_3>", "amount": 1000, "txn_type": "topup"}'
```

## Notes on Row-Level Security

Your `.env` currently connects as whichever Postgres role you used to run
`schema.sql` (likely your Mac username, which is a superuser locally) —
superusers bypass RLS, so plain CRUD works with zero extra setup.

Once you add real authentication and switch to a restricted `app_user`
DB role in production, you'll need to set `app.current_user_id` and
`app.current_org_ids` per request before RLS-protected queries will
return any rows. See the comment in `app/database.py` for exactly how.
