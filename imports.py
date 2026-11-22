from __future__ import annotations

import csv
import io
import re
from typing import Any

MAX_IMPORT_BYTES = 2 * 1024 * 1024
MAX_IMPORT_ROWS = 500
ALLOWED_STATUSES = {"New", "Contacted", "Qualified", "Follow-up", "Won", "Lost"}
ALLOWED_SOURCES = {"Website inquiry", "LinkedIn", "Referral", "Cold outreach", "Other"}

ALIASES = {
    "contact": "name",
    "contact_name": "name",
    "organization": "company",
    "company_name": "company",
    "job_title": "role",
    "title": "role",
    "interest": "need",
    "requirement": "need",
    "pipeline_stage": "status",
    "stage": "status",
}


def _header(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", (value or "").strip().lower()).strip("_")
    return ALIASES.get(key, key)


def parse_prospect_csv(
    content: bytes,
    existing_leads: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, str]], list[str]]:
    """Validate a small CSV import and skip duplicates without writing anything."""
    if not content:
        return [], ["The file is empty."]
    if len(content) > MAX_IMPORT_BYTES:
        return [], ["The file is larger than the 2 MB import limit."]

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], ["Use a UTF-8 encoded CSV file."]

    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        raw_headers = reader.fieldnames or []
        headers = [_header(h) for h in raw_headers]
        if not headers or not {"name", "company", "need"}.issubset(set(headers)):
            return [], ["CSV must include Contact name, Company, and Need columns."]
        if len(headers) != len(set(headers)):
            return [], ["The CSV contains duplicate column names."]
        reader.fieldnames = headers

        existing_keys = {
            (str(item.get("name", "")).strip().casefold(), str(item.get("company", "")).strip().casefold())
            for item in (existing_leads or [])
        }
        accepted: list[dict[str, str]] = []
        errors: list[str] = []

        for row_number, raw in enumerate(reader, start=2):
            if row_number - 1 > MAX_IMPORT_ROWS:
                errors.append(f"Only the first {MAX_IMPORT_ROWS} data rows can be imported.")
                break
            if not any(str(value or "").strip() for value in raw.values()):
                continue

            lead = {key: str(raw.get(key) or "").strip() for key in headers}
            name, company, need = lead.get("name", ""), lead.get("company", ""), lead.get("need", "")
            if not name or not company or not need:
                errors.append(f"Row {row_number}: contact name, company, and need are required.")
                continue

            email = lead.get("email", "")
            if email and ("@" not in email or "." not in email.rsplit("@", 1)[-1]):
                errors.append(f"Row {row_number}: email address is invalid.")
                continue

            status = lead.get("status", "") or "New"
            if status not in ALLOWED_STATUSES:
                errors.append(f"Row {row_number}: unsupported pipeline stage '{status}'.")
                continue

            source = lead.get("source", "") or "Other"
            if source not in ALLOWED_SOURCES:
                source = "Other"

            key = (name.casefold(), company.casefold())
            if key in existing_keys:
                errors.append(f"Row {row_number}: duplicate contact skipped ({name} at {company}).")
                continue
            existing_keys.add(key)

            accepted.append({
                "name": name,
                "company": company,
                "role": lead.get("role", "") or "Not specified",
                "source": source,
                "email": email,
                "need": need,
                "notes": lead.get("notes", ""),
                "status": status,
                "last_touch": "Imported",
            })

        return accepted, errors
    except csv.Error:
        return [], ["The CSV could not be read. Check its quoting and formatting."]
