"""Sending the letter, and recognising the reply.

The letter goes out from fihy's own domain carrying the reporter's name. It
cannot go out *as* them: a message with their address in `From`, sent from this
server, fails DMARC alignment and is rejected outright. What it can do is say
who it is for, and route the reply back so they can read it.
"""
import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr, make_msgid, parseaddr
from secrets import token_hex

import anyio

from .config import Settings, get_settings

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Attachment:
    filename: str
    content: bytes
    credit: str


@dataclass(frozen=True)
class OutboundEmail:
    to: str
    sender: str
    sender_name: str
    reply_to: str
    subject: str
    body: str
    message_id: str
    attachments: list[Attachment]


def new_reply_token() -> str:
    """Unguessable, so the address itself cannot be used to forge a reply."""
    return token_hex(12)


def reply_address(token: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    return f"r.{token}@{settings.mail_reply_domain}"


def token_from_address(address: str) -> str | None:
    """Pull the token back out of whatever the provider hands us: a bare
    address, a display-name form, or a plus-addressed variant."""
    _, bare = parseaddr(address or "")
    local = bare.split("@", 1)[0] if "@" in bare else bare
    local = local.split("+", 1)[0]
    if not local.startswith("r."):
        return None
    token = local[2:]
    return token or None


def compose(message: OutboundEmail) -> EmailMessage:
    mail = EmailMessage()
    # The reporter's name, but never their address: this server is not
    # authorised to send from it, and saying otherwise fails DMARC.
    mail["From"] = formataddr((message.sender_name, message.sender))
    mail["To"] = message.to
    mail["Reply-To"] = message.reply_to
    mail["Subject"] = message.subject
    mail["Message-ID"] = message.message_id
    mail["Auto-Submitted"] = "auto-generated"
    mail.set_content(message.body)
    for attachment in message.attachments:
        mail.add_attachment(
            attachment.content,
            maintype="image",
            subtype="jpeg",
            filename=attachment.filename,
        )
    return mail


class MailTransport:
    async def send(self, message: OutboundEmail) -> str | None:
        raise NotImplementedError


class NullMailTransport(MailTransport):
    """The default. Writes the letter to the log and delivers nothing."""

    async def send(self, message: OutboundEmail) -> str | None:
        log.warning(
            "no SMTP configured; not sending.\nTo: %s\nFrom: %s\nReply-To: %s\n"
            "Subject: %s\n%s\n(%d attachment(s))",
            message.to,
            message.sender,
            message.reply_to,
            message.subject,
            message.body,
            len(message.attachments),
        )
        return None


class SmtpTransport(MailTransport):
    """stdlib smtplib on a worker thread rather than another dependency."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _send(self, message: OutboundEmail) -> str:
        settings = self._settings
        mail = compose(message)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_starttls:
                server.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            # The envelope sender is the reply address, so a bounce comes back
            # to the same place a reply would and lands on the right report.
            server.send_message(mail, from_addr=message.reply_to, to_addrs=[message.to])
        return message.message_id

    async def send(self, message: OutboundEmail) -> str | None:
        return await anyio.to_thread.run_sync(self._send, message)


_transport: MailTransport | None = None


def get_transport() -> MailTransport:
    global _transport
    if _transport is None:
        settings = get_settings()
        if settings.mail_configured:
            _transport = SmtpTransport(settings)
        else:
            log.info("no SMTP configured; letters are not sent")
            _transport = NullMailTransport()
    return _transport


def set_transport(transport: MailTransport | None) -> None:
    global _transport
    _transport = transport


def build_message_id(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    return make_msgid(domain=settings.mail_from_domain or "fihy.invalid")
