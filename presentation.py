import html


def safe_html_text(value: object) -> str:
    """Escape untrusted text before embedding it in trusted HTML markup."""
    return html.escape(str(value or ""), quote=True)
