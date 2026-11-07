"""Writes the Dify tool YAML + Python files for Reelspan from one spec."""
import sys
import textwrap
from pathlib import Path

import yaml

# python scripts/generate_tools.py  (from the repository root) rewrites tools/*.yaml and tools/*.py
root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
NETS = "tiktok, youtube, instagram, facebook, x, threads, linkedin, pinterest, bluesky, reddit, google_business, telegram, discord, slack, mastodon, nostr, lemmy, devto, hashnode, wordpress, whop, listmonk"


def P(name, type="string", required=False, label=None, desc="", form="llm", **kw):
    d = {"name": name, "type": type, "required": required, "label": {"en_US": label or name.replace("_", " ").capitalize()},
         "human_description": {"en_US": desc}, "llm_description": desc, "form": form}
    d.update(kw)
    return d


profile = P("profile", required=True, label="Profile", desc="The Reelspan profile username whose connected accounts post (see List profiles)")
platforms = P("platforms", required=True, label="Networks", desc=f"Comma-separated networks: {NETS}")
common = [
    P("scheduled_date", label="Schedule for", desc="Publish later: ISO-8601 date-time. Leave empty to post now."),
    P("timezone", label="Timezone", desc="IANA timezone for the scheduled time, e.g. Europe/Berlin"),
    P("add_to_queue", type="boolean", label="Add to queue", desc="Take the profile's next free queue slot", form="form", default=False),
    P("first_comment", label="First comment", desc="Posted as the first comment"),
    P("settings", label="Network settings (JSON)", desc='Other API fields as JSON, e.g. {"privacy_level": "PUBLIC_TO_EVERYONE", "reddit_subreddit": "videos"}'),
    P("wait", type="boolean", label="Wait for results", desc="Wait until every network has finished", form="form", default=True),
]
caption = P("caption", label="Caption", desc="Caption, or the YouTube title")
WAIT = "return finish(c, r, p.get('wait', True) is not False)"

TOOLS = [
    ("upload_text", "Publish text", "Publish or schedule a text post to X, Threads, LinkedIn, Bluesky, Facebook, Mastodon, Discord, Telegram and more. Long text becomes a thread on X and Bluesky.",
     [profile, platforms, P("text", required=True, label="Text", desc="The post text")] + common,
     ["c = client(self.runtime.credentials)", "r = c.posts.text(p['profile'], items(p['platforms']), p['text'], **post_options(p))", WAIT]),
    ("upload_video", "Publish video", "Publish or schedule a video to TikTok, YouTube, Instagram, Facebook, X, LinkedIn, Pinterest, Reddit and more, from an uploaded file or a public URL.",
     [profile, platforms, P("video", type="file", label="Video file", desc="An uploaded video file"), P("video_url", label="Video URL", desc="Or a public https URL (Google Drive and Dropbox links work)"), caption, P("description", label="Description", desc="Longer description where the network has one")] + common,
     ["c = client(self.runtime.credentials)", "video = file_input(p.get('video')) or p.get('video_url')", "if not video:", "    raise ValueError('Give a video file or video_url.')", "r = c.posts.video(p['profile'], items(p['platforms']), video, p.get('caption') or None, **post_options(p))", WAIT]),
    ("upload_photos", "Publish photos", "Publish or schedule one photo or a carousel (in order) to Instagram, TikTok, Facebook, X, LinkedIn, Pinterest, Threads, Bluesky and more.",
     [profile, platforms, P("photos", type="files", label="Photo files", desc="Uploaded images, in order"), P("photo_urls", label="Photo URLs", desc="Or public https URLs, comma-separated, in order"), caption, P("alt_texts", label="Alt texts", desc="Alt text per photo, one per line, in order")] + common,
     ["c = client(self.runtime.credentials)", "photos = list(file_input(p.get('photos')) or []) + items(p.get('photo_urls'))", "if not photos:", "    raise ValueError('Give photo files or photo_urls.')", "alts = [a.strip() for a in str(p.get('alt_texts') or '').splitlines() if a.strip()] or None", "r = c.posts.photos(p['profile'], items(p['platforms']), photos, p.get('caption') or None, alt_texts=alts, **post_options(p))", WAIT]),
    ("upload_document", "Publish document", "Publish a PDF (or PPT/DOCX) to LinkedIn as a swipeable document.",
     [profile, P("document", type="file", label="Document file", desc="An uploaded PDF"), P("document_url", label="Document URL", desc="Or a public https URL of the PDF"), P("title", required=True, label="Title", desc="The document title")] + common,
     ["c = client(self.runtime.credentials)", "doc = file_input(p.get('document')) or p.get('document_url')", "if not doc:", "    raise ValueError('Give a document file or document_url.')", "r = c.posts.document(p['profile'], doc, p['title'], **post_options(p))", WAIT]),
    ("get_status", "Get post status", "Each network's result and link for a post, by request_id (or job_id for a scheduled post).",
     [P("request_id", label="Request ID", desc="The request_id from a publish tool"), P("job_id", label="Job ID", desc="Or a scheduled post's job_id")],
     ["if not p.get('request_id') and not p.get('job_id'):", "    raise ValueError('Give request_id or job_id.')", "return client(self.runtime.credentials).posts.status(request_id=p.get('request_id') or None, job_id=p.get('job_id') or None)"]),
    ("retry_post", "Retry failed networks", "Send the networks that failed again, with the media Reelspan already has.",
     [P("request_id", required=True, label="Request ID", desc="The post's request_id"), P("platforms", label="Networks", desc="Only these, comma-separated; empty for every failed network")],
     ["return client(self.runtime.credentials).posts.retry(p['request_id'], platforms=items(p.get('platforms')) or None)"]),
    ("list_profiles", "List profiles", "List Reelspan profiles (brands) and the networks each has connected. Use it to find the profile username.",
     [],
     ["r = client(self.runtime.credentials).profiles.list()", "return {'profiles': [{'username': x['username'], 'name': x.get('display_name'), 'networks': [k for k, v in (x.get('social_accounts') or {}).items() if v]} for x in r.get('profiles', [])]}"]),
    ("get_history", "Get post history", "Recent posts, one row per network, newest first.",
     [P("profile", label="Profile", desc="Only this profile"), P("platform", label="Network", desc="Only this network"), P("status", type="select", label="Status", desc="Only successes or failures", options=[{"value": "success", "label": {"en_US": "Success"}}, {"value": "failed", "label": {"en_US": "Failed"}}]), P("limit", type="number", label="Limit", desc="10, 20 or 50", default=20)],
     ["q = {'profile_username': p.get('profile'), 'platform': p.get('platform'), 'status': p.get('status'), 'limit': int(p.get('limit') or 20)}", "return {'history': client(self.runtime.credentials).posts.history(**{k: v for k, v in q.items() if v}).get('history', [])}"]),
    ("get_analytics", "Get analytics", "Followers, reach and engagement of a profile per network; with days, a day-by-day history; with request_id, one post's numbers.",
     [P("profile", label="Profile", desc="The profile username"), P("days", type="number", label="Days", desc="Day-by-day history of this many days"), P("request_id", label="Post request ID", desc="One post's numbers instead")],
     ["c = client(self.runtime.credentials)", "if p.get('request_id'):", "    return c.analytics.post(p['request_id'])", "if not p.get('profile'):", "    raise ValueError('Give profile (or request_id for one post).')", "return c.analytics.history(p['profile'], days=int(p['days'])) if p.get('days') else c.analytics.account(p['profile'])"]),
    ("list_scheduled", "List scheduled posts", "Posts waiting for their scheduled time.",
     [P("profile", label="Profile", desc="Only this profile")],
     ["return client(self.runtime.credentials).scheduled.list(**({'profile_username': p['profile']} if p.get('profile') else {}))"]),
    ("cancel_scheduled", "Cancel scheduled post", "Cancel a scheduled post so it is never published.",
     [P("job_id", required=True, label="Job ID", desc="The scheduled post's job_id")],
     ["return client(self.runtime.credentials).scheduled.cancel(p['job_id'])"]),
    ("write_captions", "Write captions", "Write a caption for each network from a short description of the post (uses one Reelspan AI credit).",
     [P("text", required=True, label="About the post", desc="What the post is about"), P("platforms", label="Networks", desc="Comma-separated; empty for the usual ones"), P("language", label="Language", desc="e.g. en, es, de")],
     ["return client(self.runtime.credentials).ai.write_captions(text=p['text'], platforms=items(p.get('platforms')) or None, language=p.get('language') or None, kind='text')"]),
]

TEMPLATE = '''"""{label}: {desc}"""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.common import client, compact, error_text, file_input, finish, items, post_options  # noqa: F401


class {cls}(Tool):
    def run(self, p: dict[str, Any]) -> Any:
{body}

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = compact(self.run(tool_parameters))
        except Exception as e:  # noqa: BLE001 - shown to the user and the model
            yield self.create_text_message(error_text(e))
            return
        yield self.create_json_message(result)
'''

for name, label, desc, params, body in TOOLS:
    spec = {"identity": {"name": name, "author": "reelspan", "label": {"en_US": label}},
            "description": {"human": {"en_US": desc}, "llm": desc},
            "parameters": params,
            "extra": {"python": {"source": f"tools/{name}.py"}}}
    with open(root / "tools" / f"{name}.yaml", "w", encoding="utf8", newline="\n") as f:
        yaml.safe_dump(spec, f, sort_keys=False, allow_unicode=True, width=200)
    cls = "".join(w.capitalize() for w in name.split("_")) + "Tool"
    with open(root / "tools" / f"{name}.py", "w", encoding="utf8", newline="\n") as f:
        f.write(TEMPLATE.format(label=label, desc=desc, cls=cls, body=textwrap.indent("\n".join(body), " " * 8)))
    print(f"  - tools/{name}.yaml")
