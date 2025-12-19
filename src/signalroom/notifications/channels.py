"""Notification channel implementations."""

from signalroom.common import get_logger, settings

log = get_logger(__name__)


async def send_slack(message: str, channel_id: str | None = None) -> None:
    """Send a message to Slack.

    Args:
        message: Message text (supports Slack markdown).
        channel_id: Slack channel ID. Defaults to settings.
    """
    from slack_sdk.web.async_client import AsyncWebClient

    channel_id = channel_id or settings.slack_channel_id
    token = settings.slack_bot_token.get_secret_value()

    if not token:
        log.warning("slack_not_configured")
        return

    client = AsyncWebClient(token=token)

    response = await client.chat_postMessage(
        channel=channel_id,
        text=message,
    )

    log.info("slack_sent", channel=channel_id, ts=response.get("ts"))


async def send_email(
    to: str,
    subject: str,
    html: str,
    from_email: str | None = None,
) -> None:
    """Send an email via Resend.

    Args:
        to: Recipient email address.
        subject: Email subject.
        html: HTML body content.
        from_email: Sender email. Defaults to settings.
    """
    import resend

    api_key = settings.resend_api_key.get_secret_value()
    from_email = from_email or settings.resend_from_email

    if not api_key:
        log.warning("resend_not_configured")
        return

    resend.api_key = api_key

    # Resend's SDK is sync, but simple enough to call directly
    response = resend.Emails.send(
        {
            "from": from_email,
            "to": to,
            "subject": subject,
            "html": html,
        }
    )

    log.info("email_sent", to=to, id=response.get("id"))


async def send_sms(to: str, message: str, from_number: str | None = None) -> None:
    """Send an SMS via Twilio.

    Args:
        to: Recipient phone number (E.164 format, e.g., +15551234567).
        message: Message text.
        from_number: Sender phone number. Defaults to settings.
    """
    from twilio.rest import Client

    account_sid = settings.twilio_account_sid
    auth_token = settings.twilio_auth_token.get_secret_value()
    from_number = from_number or settings.twilio_from_number

    if not auth_token:
        log.warning("twilio_not_configured")
        return

    client = Client(account_sid, auth_token)

    # Twilio's SDK is sync
    message_obj = client.messages.create(
        body=message,
        from_=from_number,
        to=to,
    )

    log.info("sms_sent", to=to, sid=message_obj.sid)
