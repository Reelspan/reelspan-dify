"""Publish text: Publish or schedule a text post to X, Threads, LinkedIn, Bluesky, Facebook, Mastodon, Discord, Telegram and more. Long text becomes a thread on X and Bluesky."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.common import client, compact, error_text, file_input, finish, items, post_options  # noqa: F401


class UploadTextTool(Tool):
    def run(self, p: dict[str, Any]) -> Any:
        c = client(self.runtime.credentials)
        r = c.posts.text(p['profile'], items(p['platforms']), p['text'], **post_options(p))
        return finish(c, r, p.get('wait', True) is not False)

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = compact(self.run(tool_parameters))
        except Exception as e:  # noqa: BLE001 - shown to the user and the model
            yield self.create_text_message(error_text(e))
            return
        yield self.create_json_message(result)
