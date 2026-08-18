"""Content-negotiation helper for routes that serve both a Jinja2 page and a JSON API.

The JSON-side counterpart to main.py's HTML-error-page negotiation: existing callers
(browser navigations, the app's own fetch() calls that don't set Accept) are completely
unaffected, since nothing today sends "application/json" as Accept. Only a caller that
explicitly asks for JSON gets the new response shape.
"""
from fastapi import Request


def wants_json(request: Request) -> bool:
    """True if the caller explicitly prefers a JSON response over HTML."""
    return "application/json" in request.headers.get("accept", "")
