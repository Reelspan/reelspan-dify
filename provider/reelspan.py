from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from utils.common import client, error_text


class ReelspanProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        if not credentials.get("reelspan_api_key"):
            raise ToolProviderCredentialValidationError("Enter your Reelspan API key.")
        try:
            client(credentials).me()
        except Exception as e:  # noqa: BLE001
            raise ToolProviderCredentialValidationError(error_text(e)) from e
