"""Get analytics: Followers, reach and engagement of a profile per network; with days, a day-by-day history; with request_id, one post's numbers."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.common import client, compact, error_text, file_input, finish, items, post_options  # noqa: F401


class GetAnalyticsTool(Tool):
    def run(self, p: dict[str, Any]) -> Any:
        c = client(self.runtime.credentials)
        if p.get('request_id'):
            return c.analytics.post(p['request_id'])
        if not p.get('profile'):
            raise ValueError('Give profile (or request_id for one post).')
        return c.analytics.history(p['profile'], days=int(p['days'])) if p.get('days') else c.analytics.account(p['profile'])

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = compact(self.run(tool_parameters))
        except Exception as e:  # noqa: BLE001 - shown to the user and the model
            yield self.create_text_message(error_text(e))
            return
        yield self.create_json_message(result)
