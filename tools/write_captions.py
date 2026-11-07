"""Write captions: Write a caption for each network from a short description of the post (uses one Reelspan AI credit)."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.common import client, compact, error_text, file_input, finish, items, post_options  # noqa: F401


class WriteCaptionsTool(Tool):
    def run(self, p: dict[str, Any]) -> Any:
        return client(self.runtime.credentials).ai.write_captions(text=p['text'], platforms=items(p.get('platforms')) or None, language=p.get('language') or None, kind='text')

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = compact(self.run(tool_parameters))
        except Exception as e:  # noqa: BLE001 - shown to the user and the model
            yield self.create_text_message(error_text(e))
            return
        yield self.create_json_message(result)
