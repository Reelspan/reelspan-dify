"""Get post status: Each network's result and link for a post, by request_id (or job_id for a scheduled post)."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.common import client, compact, error_text, file_input, finish, items, post_options  # noqa: F401


class GetStatusTool(Tool):
    def run(self, p: dict[str, Any]) -> Any:
        if not p.get('request_id') and not p.get('job_id'):
            raise ValueError('Give request_id or job_id.')
        return client(self.runtime.credentials).posts.status(request_id=p.get('request_id') or None, job_id=p.get('job_id') or None)

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = compact(self.run(tool_parameters))
        except Exception as e:  # noqa: BLE001 - shown to the user and the model
            yield self.create_text_message(error_text(e))
            return
        yield self.create_json_message(result)
