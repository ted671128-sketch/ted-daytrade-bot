import logging

from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    FlexContainer,
    FlexMessage,
    MessagingApi,
    PushMessageRequest,
    ReplyMessageRequest,
    TextMessage,
)

from app.config import settings

log = logging.getLogger(__name__)
_config = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)


def _flex(alt_text: str, contents: dict) -> FlexMessage:
    return FlexMessage(alt_text=alt_text, contents=FlexContainer.from_dict(contents))


def push_text(text: str, user_id: str | None = None) -> None:
    to = user_id or settings.LINE_USER_ID
    if not to:
        log.warning("LINE_USER_ID 未設定，無法推播")
        return
    with ApiClient(_config) as client:
        MessagingApi(client).push_message(
            PushMessageRequest(to=to, messages=[TextMessage(text=text)])
        )


def push_flex(alt_text: str, contents: dict, user_id: str | None = None) -> None:
    to = user_id or settings.LINE_USER_ID
    if not to:
        log.warning("LINE_USER_ID 未設定，無法推播")
        return
    with ApiClient(_config) as client:
        MessagingApi(client).push_message(
            PushMessageRequest(to=to, messages=[_flex(alt_text, contents)])
        )


def reply_text(reply_token: str, text: str) -> None:
    with ApiClient(_config) as client:
        MessagingApi(client).reply_message(
            ReplyMessageRequest(
                reply_token=reply_token, messages=[TextMessage(text=text)]
            )
        )


def reply_flex(reply_token: str, alt_text: str, contents: dict) -> None:
    with ApiClient(_config) as client:
        MessagingApi(client).reply_message(
            ReplyMessageRequest(
                reply_token=reply_token, messages=[_flex(alt_text, contents)]
            )
        )
