import html
import re


def safe_html_text(value: object) -> str:
    """Escape untrusted text before embedding it in trusted HTML markup."""
    return html.escape(str(value or ""), quote=True)


def safe_csv_value(value: object) -> str:
    """Prefix spreadsheet formula-like values so CSV exports open as text."""
    text = "" if value is None else str(value)
    if re.match(r"^[\t\r\n ]*[=+\-@]", text):
        return "'" + text
    return text

 
def matches_lead_search(lead: dict[str, object], query: str) -> bool:
    """Search all useful prospect fields without case sensitivity."""
    needle = str(query or "").strip().casefold()
    if not needle:
        return True
    searchable = " ".join(
        str(lead.get(field, "") or "")
        for field in ("name", "company", "role", "source", "email", "need", "notes", "status", "last_touch")
    )
    return needle in searchable.casefold()
