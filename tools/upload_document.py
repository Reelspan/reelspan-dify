"""Publish document: Publish a PDF (or PPT/DOCX) to LinkedIn as a swipeable document."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.common import client, compact, error_text, file_input, finish, items, post_options  # noqa: F401


class UploadDocumentTool(Tool):
    def run(self, p: dict[str, Any]) -> Any:
        c = client(self.runtime.credentials)
        doc = file_input(p.get('document')) or p.get('document_url')
        if not doc:
            raise ValueError('Give a document file or document_url.')
        r = c.posts.document(p['profile'], doc, p['title'], **post_options(p))
        return finish(c, r, p.get('wait', True) is not False)

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = compact(self.run(tool_parameters))
        except Exception as e:  # noqa: BLE001 - shown to the user and the model
            yield self.create_text_message(error_text(e))
            return
        yield self.create_json_message(result)
