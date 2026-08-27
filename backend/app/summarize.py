"""Plain-language summaries of an issue and what people have said about it.

Same shape as `otp.set_sender`: an interface with a real implementation and a
no-op default, so a checkout runs with no API key and the field is simply null.
"""
import logging
from dataclasses import dataclass

from .config import Settings, get_settings

log = logging.getLogger(__name__)

SYSTEM = """You write one-paragraph summaries of civic issue reports for a \
public app used in India.

Write 2 to 3 sentences, at most 60 words. Say what the problem is, where it is \
if the report says, and what people who have since visited have added. Use \
plain language a resident would use.

Report only what the text says. Do not guess at causes, do not suggest fixes, \
do not estimate danger, and do not invent detail that is not there. If the \
report and replies say very little, write one short sentence and stop.

Reply with the summary itself. No preamble, no heading, no quotation marks."""


@dataclass(frozen=True)
class SummaryRequest:
    title: str
    description: str
    category: str
    severity: str
    status: str
    locality: str | None
    # What people who came later wrote, oldest first.
    voices: list[str]


def render(request: SummaryRequest) -> str:
    lines = [
        f"Category: {request.category}",
        f"Reported severity: {request.severity}",
        f"Current status: {request.status}",
    ]
    if request.locality:
        lines.append(f"Locality: {request.locality}")
    lines.append(f"\nTitle: {request.title}")
    if request.description:
        lines.append(f"Reporter wrote: {request.description}")
    if request.voices:
        lines.append("\nOthers who visited since wrote:")
        lines.extend(f"- {voice}" for voice in request.voices)
    else:
        lines.append("\nNobody else has written anything yet.")
    return "\n".join(lines)


class Summarizer:
    async def summarize(self, request: SummaryRequest) -> str | None:
        raise NotImplementedError


class NullSummarizer(Summarizer):
    """The default. No key, no summary, and the field stays null."""

    async def summarize(self, request: SummaryRequest) -> str | None:
        return None


class ClaudeSummarizer(Summarizer):
    def __init__(self, settings: Settings) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.ai_summary_model

    async def summarize(self, request: SummaryRequest) -> str | None:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=2000,
            system=SYSTEM,
            # A short factual restatement of text already in hand. Low effort
            # is the right setting, and leaving thinking on avoids the
            # tag-leakage that disabling it invites.
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": render(request)}],
        )
        if response.stop_reason == "refusal":
            log.warning(
                "summary refused for %r (%s)",
                request.title,
                response.stop_details.category if response.stop_details else None,
            )
            return None
        text = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        return text or None


_summarizer: Summarizer | None = None


def get_summarizer() -> Summarizer:
    global _summarizer
    if _summarizer is None:
        settings = get_settings()
        if settings.ai_summary_configured:
            _summarizer = ClaudeSummarizer(settings)
        else:
            log.info("no ANTHROPIC_API_KEY; issue summaries are off")
            _summarizer = NullSummarizer()
    return _summarizer


def set_summarizer(summarizer: Summarizer | None) -> None:
    global _summarizer
    _summarizer = summarizer
