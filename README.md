# SalesPilot

SalesPilot is a lightweight sales workspace for managing a small prospect pipeline.

## Current capabilities

- Prospect dashboard with pipeline and priority summaries
- Search and filter by company, contact, stage, and priority
- Rule-based lead scoring with suggested next steps
- Add and edit prospect records with basic field validation
- Update pipeline stage and mark follow-up activity
- Editable outreach drafts and CSV export
- Optional Supabase authentication and per-user persistent lead storage

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Enable accounts and persistent storage

The app stays in clearly labelled demo mode until both `SUPABASE_URL` and `SUPABASE_ANON_KEY` are configured in Streamlit secrets.

1. Create a free Supabase project.
2. In the Supabase SQL Editor, run the migration in `database/migrations/001_create_leads.sql`.
3. In Supabase project settings, copy the Project URL and the public anon/publishable key. Never use the service-role key in this app.
4. In Streamlit Community Cloud, open the app's **Settings → Secrets** and add:

```toml
SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"
SUPABASE_ANON_KEY = "YOUR_PUBLIC_ANON_KEY"
```

5. Restart the Streamlit app. Visitors will then see sign-in and account creation instead of the shared sample dashboard.

Supabase Auth email confirmation settings apply to new accounts. The app uses the public anon key and relies on PostgreSQL row-level security; each authenticated account can access only rows whose `user_id` matches its auth user ID.

## Public demo

https://salespilot-demo.streamlit.app/

## Important limitations

- Without Supabase secrets, the public app runs in demo mode with fictional leads held only in Streamlit session state.
- With Supabase configured, lead records persist in PostgreSQL and are scoped by authenticated user.
- The app currently has no password-reset screen, team sharing, external CRM connection, AI provider, or outbound email/phone integration.
- Lead scoring and outreach suggestions are rule-based, not AI-generated. Reply drafts are never sent.
- CSV exports prefix formula-like user content so spreadsheet applications treat it as text.\n- Supabase leaked-password screening is Pro-plan-only; this project intentionally remains on the Free plan, so the related Security Advisor warning is an accepted limitation under the $0 constraint. Do not enter sensitive or real customer data until account recovery and operational security have been reviewed.\n- Use fictional data until you have reviewed the deployment's privacy, account-recovery, and operational requirements.

## Validation

GitHub Actions compiles the app and tests, runs the storage and HTML-escaping unit tests, and starts the app with Streamlit AppTest on pushes and pull requests to `main`.

Run the unit tests locally with:

```bash
python -m unittest discover -s tests -v
```
