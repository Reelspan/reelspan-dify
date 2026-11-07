"""Publish video: Publish or schedule a video to TikTok, YouTube, Instagram, Facebook, X, LinkedIn, Pinterest, Reddit and more, from an uploaded file or a public URL."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.common import client, compact, error_text, file_input, finish, items, post_options  # noqa: F401


class UploadVideoTool(Tool):
    def run(self, p: dict[str, Any]) -> Any:
        c = client(self.runtime.credentials)
        video = file_input(p.get('video')) or p.get('video_url')
        if not video:
            raise ValueError('Give a video file or video_url.')
        r = c.posts.video(p['profile'], items(p['platforms']), video, p.get('caption') or None, **post_options(p))
        return finish(c, r, p.get('wait', True) is not False)

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = compact(self.run(tool_parameters))
        except Exception as e:  # noqa: BLE001 - shown to the user and the model
            yield self.create_text_message(error_text(e))
            return
        yield self.create_json_message(result)
