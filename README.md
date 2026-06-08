# SmartSociety Backend

## Supabase Setup

1. Copy `backend/.env.example` to `backend/.env`.
2. Set `DATABASE_URL` to the Supabase Postgres connection string.
   It must look like `postgresql+psycopg2://...`, not `https://<project>.supabase.co`.
3. Install dependencies from `backend/requirements.txt`.
4. Run explicit schema patches when needed:

```powershell
backend\myenv\Scripts\python.exe -m app.database.migrate
```

5. Start the API server.

## Interview Notes

- The backend is configured for Supabase Postgres only. Local `DB_HOST`/`DB_NAME` fallback is not used.
- `AUTO_CREATE_TABLES` and `AUTO_PATCH_SCHEMA` are meant for local convenience only.
- For a cleaner demo story, prefer running `python -m app.database.migrate` before startup instead of relying on automatic patching.
- Keep `backend/.env` out of version control and rotate any shared secrets before deployment.
