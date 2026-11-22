from __future__ import annotations

from typing import Any

from supabase import Client, create_client


LEAD_FIELDS = (
    "name",
    "company",
    "role",
    "source",
    "email",
    "need",
    "notes",
    "status",
    "last_touch",
)


def get_supabase_client(url: str, anon_key: str) -> Client:
    """Create a client using the public anon key; table access is protected by RLS."""
    return create_client(url, anon_key)


def _payload(lead: dict[str, Any], user_id: str) -> dict[str, Any]:
    return {**{field: str(lead.get(field, "")) for field in LEAD_FIELDS}, "user_id": user_id}


def _normalise(row: dict[str, Any]) -> dict[str, Any]:
    return {**{field: row.get(field, "") for field in LEAD_FIELDS}, "id": row["id"]}


def load_or_seed_leads(
    client: Client,
    user_id: str,
    initial_leads: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Load only this authenticated user's leads; seed fictional examples once if empty."""
    result = (
        client.table("leads")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )
    rows = result.data or []
    if not rows and initial_leads:
        seed_rows = [_payload(lead, user_id) for lead in initial_leads]
        inserted = client.table("leads").insert(seed_rows).execute()
        rows = inserted.data or []
    return [_normalise(row) for row in rows]


def insert_lead(client: Client, user_id: str, lead: dict[str, Any]) -> dict[str, Any]:
    result = client.table("leads").insert(_payload(lead, user_id)).execute()
    if not result.data:
        raise RuntimeError("The database did not return the saved prospect.")
    return _normalise(result.data[0])


def update_lead(client: Client, user_id: str, lead: dict[str, Any]) -> None:
    lead_id = lead.get("id")
    if not lead_id:
        raise ValueError("Cannot update a prospect without its database ID.")
    payload = {field: str(lead.get(field, "")) for field in LEAD_FIELDS}
    result = (
        client.table("leads")
        .update(payload)
        .eq("id", lead_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise RuntimeError("The prospect was not updated.")
