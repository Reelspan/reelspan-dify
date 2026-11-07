"""Get post history: Recent posts, one row per network, newest first."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.common import client, compact, error_text, file_input, finish, items, post_options  # noqa: F401


class GetHistoryTool(Tool):
    def run(self, p: dict[str, Any]) -> Any:
        q = {'profile_username': p.get('profile'), 'platform': p.get('platform'), 'status': p.get('status'), 'limit': int(p.get('limit') or 20)}
        return {'history': client(self.runtime.credentials).posts.history(**{k: v for k, v in q.items() if v}).get('history', [])}

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = compact(self.run(tool_parameters))
        except Exception as e:  # noqa: BLE001 - shown to the user and the model
            yield self.create_text_message(error_text(e))
            return
        yield self.create_json_message(result)
