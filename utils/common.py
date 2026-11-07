"""Shared by every Reelspan tool: the client, input parsing and trimming answers for the model."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from reelspan import Reelspan, ReelspanError

VERSION = "0.1.0"


def client(credentials: Dict[str, Any]) -> Reelspan:
    return Reelspan(
        api_key=credentials.get("reelspan_api_key"),
        base_url=credentials.get("base_url") or None,
        headers={"x-reelspan-client": f"dify/{VERSION}"},
    )


def items(value: Any) -> List[str]:
    """A list from a list, a JSON array, or comma/newline-separated text."""
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if text.startswith("["):
        try:
            return [str(v).strip() for v in json.loads(text) if str(v).strip()]
        except ValueError:
            pass
    return [p.strip() for p in text.replace("\n", ",").split(",") if p.strip()]


def settings(value: Any) -> Optional[Dict[str, Any]]:
    if not value:
        return None
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
    except ValueError as e:
        raise ValueError(f"settings must be a JSON object, e.g. {{\"privacy_level\": \"PUBLIC_TO_EVERYONE\"}} ({e})") from e
    if not isinstance(parsed, dict):
        raise ValueError("settings must be a JSON object")
    return parsed


def compact(value: Any, depth: int = 0) -> Any:
    if isinstance(value, list):
        return [compact(v, depth + 1) for v in value[:100]]
    if isinstance(value, dict):
        return {k: ("…" if depth > 6 else compact(v, depth + 1)) for k, v in value.items() if v is not None and k not in ("raw", "usage")}
    return value


def post_options(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "description": p.get("description") or None,
        "scheduled_date": p.get("scheduled_date") or None,
        "timezone": p.get("timezone") or None,
        "add_to_queue": bool(p.get("add_to_queue")),
        "first_comment": p.get("first_comment") or None,
        "extra": settings(p.get("settings")),
        "async_upload": True,
    }


def finish(c: Reelspan, r: Dict[str, Any], wait: bool = True) -> Dict[str, Any]:
    """Waits for every network unless the post was scheduled or already has results."""
    if wait and r.get("request_id") and not r.get("job_id") and not r.get("results"):
        return {"request_id": r["request_id"], **c.posts.wait(r["request_id"], timeout=240)}
    return r


def file_input(f: Any) -> Any:
    """A Dify file (uploaded in the chat or workflow) as bytes with its name."""
    if f is None:
        return None
    if isinstance(f, list):
        return [file_input(x) for x in f]
    name = getattr(f, "filename", None) or getattr(f, "name", None) or "file"
    return (name, f.blob)


def error_text(e: Exception) -> str:
    if isinstance(e, ReelspanError):
        hint = " Check the API key in the Reelspan tool settings." if e.status == 401 else ""
        return f"Reelspan answered {e.status}{' ' + e.code if e.code else ''}: {e}.{hint}"
    return str(e)
