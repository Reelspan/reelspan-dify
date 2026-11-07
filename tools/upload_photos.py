"""Publish photos: Publish or schedule one photo or a carousel (in order) to Instagram, TikTok, Facebook, X, LinkedIn, Pinterest, Threads, Bluesky and more."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.common import client, compact, error_text, file_input, finish, items, post_options  # noqa: F401


class UploadPhotosTool(Tool):
    def run(self, p: dict[str, Any]) -> Any:
        c = client(self.runtime.credentials)
        photos = list(file_input(p.get('photos')) or []) + items(p.get('photo_urls'))
        if not photos:
            raise ValueError('Give photo files or photo_urls.')
        alts = [a.strip() for a in str(p.get('alt_texts') or '').splitlines() if a.strip()] or None
        r = c.posts.photos(p['profile'], items(p['platforms']), photos, p.get('caption') or None, alt_texts=alts, **post_options(p))
        return finish(c, r, p.get('wait', True) is not False)

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = compact(self.run(tool_parameters))
        except Exception as e:  # noqa: BLE001 - shown to the user and the model
            yield self.create_text_message(error_text(e))
            return
        yield self.create_json_message(result)
