"""Checks the plugin's YAML and runs every tool against a local stand-in for the API (no network)."""

import importlib.util
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dify_plugin.entities.tool import ToolInvokeMessage  # noqa: E402

SEEN: list = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle(self):
        n = int(self.headers.get("Content-Length") or 0)
        SEEN.append({"method": self.command, "path": self.path, "headers": dict(self.headers), "body": self.rfile.read(n)})
        if self.headers.get("Authorization") != "Bearer rs_dify":
            return self._reply(401, {"message": "Invalid API key", "error_code": "UNAUTHORIZED"})
        path = self.path.split("?")[0]
        routes = {
            "/v1/me": {"email": "me@example.com"},
            "/v1/profiles": {"profiles": [{"username": "acme", "display_name": "Acme", "social_accounts": {"x": {"a": 1}, "tiktok": ""}}]},
            "/v1/posts/text": {"success": True, "request_id": "req_1"},
            "/v1/posts/video": {"success": True, "job_id": "job_1"},
            "/v1/posts/photos": {"success": True, "request_id": "req_p", "results": {"instagram": {"success": True, "url": "https://instagram.com/p/1"}}},
            "/v1/posts/status": {"status": "completed", "results": [{"platform": "x", "success": True, "url": "https://x.com/1", "raw": {"x": 1}}]},
        }
        self._reply(200, routes.get(path, {"ok": True, "path": path}))

    do_GET = do_POST = do_DELETE = _handle


@pytest.fixture(scope="module")
def creds():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield {"reelspan_api_key": "rs_dify", "base_url": f"http://127.0.0.1:{server.server_address[1]}"}
    server.shutdown()
    server.server_close()


def load(rel: str):
    spec = importlib.util.spec_from_file_location(rel.replace("/", "_")[:-3], ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tool(name: str, creds):
    mod = load(f"tools/{name}.py")
    cls = next(v for k, v in vars(mod).items() if k.endswith("Tool") and k != "Tool")
    return cls.from_credentials(creds)


def messages(t, params):
    return list(t._invoke(params))


def test_manifest_and_every_tool_file_exist():
    manifest = yaml.safe_load((ROOT / "manifest.yaml").read_text(encoding="utf8"))
    assert (ROOT / "_assets" / manifest["icon"]).exists()
    assert (ROOT / manifest["privacy"]).exists()
    provider = yaml.safe_load((ROOT / manifest["plugins"]["tools"][0]).read_text(encoding="utf8"))
    assert len(provider["tools"]) == 12
    for rel in provider["tools"]:
        spec = yaml.safe_load((ROOT / rel).read_text(encoding="utf8"))
        assert (ROOT / spec["extra"]["python"]["source"]).exists()
        assert spec["description"]["llm"]
        for p in spec["parameters"]:
            assert p["form"] in ("llm", "form") and p["type"] in ("string", "number", "boolean", "select", "file", "files")


def test_credentials_are_checked(creds):
    from dify_plugin.errors.tool import ToolProviderCredentialValidationError

    provider = load("provider/reelspan.py").ReelspanProvider()
    provider._validate_credentials(creds)
    with pytest.raises(ToolProviderCredentialValidationError, match="401"):
        provider._validate_credentials({**creds, "reelspan_api_key": "bad"})


def test_upload_text_waits_and_answers_json(creds):
    [m] = messages(tool("upload_text", creds), {"profile": "acme", "platforms": "x, bluesky", "text": "Hello", "settings": '{"x_reply_settings": "following"}'})
    assert m.type == ToolInvokeMessage.MessageType.JSON
    assert m.message.json_object == {"request_id": "req_1", "status": "completed", "results": [{"platform": "x", "success": True, "url": "https://x.com/1"}]}
    body = json.loads(next(s for s in SEEN if s["path"] == "/v1/posts/text")["body"])
    assert body["platform"] == ["x", "bluesky"] and body["x_reply_settings"] == "following" and body["user"] == "acme"


class FakeFile:
    filename = "clip.mp4"
    blob = b"VIDEO-BYTES"


def test_upload_video_from_a_dify_file(creds):
    [m] = messages(tool("upload_video", creds), {"profile": "acme", "platforms": "tiktok", "video": FakeFile(), "caption": "Launch", "scheduled_date": "2026-12-01T09:00:00Z"})
    assert m.message.json_object["job_id"] == "job_1"
    body = SEEN[-1]["body"]
    assert b'filename="clip.mp4"' in body and b"VIDEO-BYTES" in body


def test_photos_from_urls(creds):
    [m] = messages(tool("upload_photos", creds), {"profile": "acme", "platforms": "instagram", "photo_urls": "https://a/1.jpg,https://a/2.jpg", "alt_texts": "One\nTwo"})
    assert m.message.json_object["results"]["instagram"]["success"] is True
    assert SEEN[-1]["body"].count(b'name="photos[]"') == 2


def test_list_profiles_and_errors_as_text(creds):
    [m] = messages(tool("list_profiles", creds), {})
    assert m.message.json_object == {"profiles": [{"username": "acme", "name": "Acme", "networks": ["x"]}]}
    [e] = messages(tool("get_status", creds), {})
    assert e.type == ToolInvokeMessage.MessageType.TEXT and "request_id or job_id" in e.message.text
    [bad] = messages(tool("list_profiles", {**creds, "reelspan_api_key": "nope"}), {})
    assert "401" in bad.message.text and "API key" in bad.message.text


@pytest.mark.parametrize("name,params", [
    ("retry_post", {"request_id": "req_1", "platforms": "x"}),
    ("get_history", {"limit": 10}),
    ("get_analytics", {"profile": "acme"}),
    ("list_scheduled", {}),
    ("cancel_scheduled", {"job_id": "job_1"}),
    ("write_captions", {"text": "New espresso blend"}),
    ("upload_document", {"profile": "acme", "document_url": "https://a/deck.pdf", "title": "Deck", "wait": False}),
])
def test_every_other_tool_runs(creds, name, params):
    [m] = messages(tool(name, creds), params)
    assert m.type == ToolInvokeMessage.MessageType.JSON, getattr(m.message, "text", "")
