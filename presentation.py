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
