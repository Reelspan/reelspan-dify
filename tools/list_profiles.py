"""List profiles: List Reelspan profiles (brands) and the networks each has connected. Use it to find the profile username."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.common import client, compact, error_text, file_input, finish, items, post_options  # noqa: F401


class ListProfilesTool(Tool):
    def run(self, p: dict[str, Any]) -> Any:
        r = client(self.runtime.credentials).profiles.list()
        return {'profiles': [{'username': x['username'], 'name': x.get('display_name'), 'networks': [k for k, v in (x.get('social_accounts') or {}).items() if v]} for x in r.get('profiles', [])]}

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = compact(self.run(tool_parameters))
        except Exception as e:  # noqa: BLE001 - shown to the user and the model
            yield self.create_text_message(error_text(e))
            return
        yield self.create_json_message(result)
