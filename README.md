# SalesPilot

SalesPilot is a lightweight sales-workspace prototype for managing a small prospect pipeline.

## Current capabilities

- Prospect dashboard with pipeline and priority summaries
- Search and filter by company, contact, stage, and priority
- Rule-based lead scoring with suggested next steps
- Add and edit prospect records with basic field validation
- Update pipeline stage and mark follow-up activity
- Edit outreach drafts and export the current pipeline to CSV

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Deployment

The public demo is hosted on Streamlit Community Cloud:
https://salespilot-demo.streamlit.app/

## Important limitations

- Prospect records currently live in Streamlit session state. They are temporary and are not shared across users or guaranteed to survive a session ending, app restart, or redeploy.
- The included leads are fictional examples. Do not enter real customer or confidential data.
- Lead scoring and outreach suggestions are rule-based, not AI-generated.
- There is no login, multi-user access control, external CRM connection, persistent database, or outbound email/phone integration yet.
- Reply drafts are editable suggestions and are never sent.

## Validation

GitHub Actions runs a Python syntax check and a Streamlit app-startup smoke test on pushes and pull requests to `main`.
