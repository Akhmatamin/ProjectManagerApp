import asyncio

import resend

from app.shared.config import Settings


class ResendAPIClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        resend.api_key = settings.resend_api_key

    def _send(self, params: dict):
        return resend.Emails.send(params)  # type: ignore

    async def send_email(self, to_email: str, subject: str, html_content: str):

        params = {
            "from": self.settings.resend_from,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        return await asyncio.to_thread(self._send, params)
