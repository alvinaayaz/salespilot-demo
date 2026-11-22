# SalesPilot

SalesPilot is a lightweight sales workspace for independent professionals and small teams who want a clearer way to manage prospects and follow-ups.

**Open SalesPilot:** https://salespilot-demo.streamlit.app/

## What you can do

- Keep prospect records in one searchable workspace
- Track each opportunity through a simple pipeline
- Review transparent, rule-based lead scores and priority signals
- See suggested next steps for each prospect
- Prepare and edit outreach drafts without sending anything automatically
- Export your pipeline to CSV

## Your workspace

Create an account to get a persistent, account-scoped workspace. New accounts start empty: your pipeline contains only the prospects you add. Existing prospect records are preserved.

The hosted app uses Supabase authentication and PostgreSQL storage. Database row-level security policies scope prospect access to the signed-in account. The app uses the public anon/publishable key; a service-role key is not used in the application.

## Product scope

SalesPilot currently focuses on prospect organization and follow-up workflow. Lead scoring and reply suggestions are rule-based, not AI-generated. The app does not currently send email or messages, sync with external CRMs, support team sharing, or provide an in-app password-reset flow.

Use fictional or non-sensitive contact information while evaluating the service. The project is intentionally operated on free hosting and database tiers; availability and performance are subject to those providers' free-plan limits.

## Local development

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

For a persistent local setup, configure `SUPABASE_URL` and `SUPABASE_ANON_KEY` in Streamlit secrets and apply `database/migrations/001_create_leads.sql` to your Supabase project. Never put a service-role key in client-facing application configuration.

## Validation

GitHub Actions compiles the application, runs the unit tests, and performs a Streamlit startup smoke test.

Run tests locally:

```bash
python -m unittest discover -s tests -v
```
