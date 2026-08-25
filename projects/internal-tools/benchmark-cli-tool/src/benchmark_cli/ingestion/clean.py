"""Source parsers plus normalization and credential redaction for ingestion."""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

_BOT_NAME = re.compile(r"(?:bot|webhook|github|ci|jenkins|dependabot)$", re.IGNORECASE)
_URL_ONLY = re.compile(r"^https?://\S+$", re.IGNORECASE)
_TIMESTAMP_GUTTER = re.compile(
    r"(?:^|\s)(?:\[?\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\]?\s*(?:-->)?|\(\d{1,2}:\d{2}\))(?:\s|$)"
)
_FILLER = re.compile(r"^(?:um+|uh+|\[inaudible\]|\[crosstalk\]|\[silence\])(?:\s+|$)", re.IGNORECASE)
_MENTION = re.compile(r"<@!?(\d+)>")
_CHANNEL = re.compile(r"<#(\d+)>")
_EMOJI = re.compile(r"<a?:([\w-]+):\d+>")
_BLANKS = re.compile(r"\n[ \t]*\n(?:[ \t]*\n)+")
_SPACE = re.compile(r"[ \t]+")
_PUNCTUATION_ONLY = re.compile(r"^[\W_]+$", re.UNICODE)
_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\b(?:bearer\s+)[A-Za-z0-9._~+/=-]{12,}\b", re.IGNORECASE),
    re.compile(r"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----.*?-----END(?: [A-Z]+)? PRIVATE KEY-----", re.DOTALL),
    re.compile(r"\bpassword\s*=\s*[^\s;]+", re.IGNORECASE),
)
_SECTION_PATTERN = re.compile(r"^\s*(?:\d+[.)]\s*)?([^:]{2,100}):(?:\s|$)")
_NUMBERED_HEADING_PATTERN = re.compile(r"^\s*\d+(?:\.\d+)*\.?\s+(.{2,100})\s*$")


@dataclass(frozen=True, slots=True)
class RawUnit:
    """One atomic source unit that chunking preserves unless it is oversize."""

    text: str
    speaker: str | None
    timestamp: datetime | None
    ordinal: int
    extra: dict[str, Any]


def _section_blocks(text: str) -> list[tuple[str, int, int]]:
    """Return heading-delimited line ranges for a policy document."""
    starts: list[tuple[str, int]] = []
    lines = text.splitlines()
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        title: str | None = None
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
        elif match := _SECTION_PATTERN.match(stripped):
            title = match.group(1).strip()
        elif match := _NUMBERED_HEADING_PATTERN.match(stripped):
            title = match.group(1).strip()
        elif number == 1 and stripped:
            title = stripped.rstrip(":")
        if title:
            starts.append((title, number))
    return [
        (title, start, starts[index + 1][1] - 1 if index + 1 < len(starts) else len(lines))
        for index, (title, start) in enumerate(starts)
    ]


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_text(text: str) -> str:
    """Normalize presentation noise and redact secrets before text reaches the API."""
    normalized = unicodedata.normalize("NFKC", text).replace("\ufeff", "").replace("\u200b", "")
    normalized = normalized.translate(str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"}))
    for pattern in _SECRET_PATTERNS:
        normalized = pattern.sub("[REDACTED]", normalized)

    in_fence = False
    lines: list[str] = []
    for line in normalized.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        line = line.rstrip()
        if not in_fence:
            line = _SPACE.sub(" ", line)
        if line.strip() and _PUNCTUATION_ONLY.match(line.strip()):
            continue
        lines.append(line)
    return _BLANKS.sub("\n\n", "\n".join(lines)).strip()


def _rewrite_discord(text: str, users: dict[str, str], channels: dict[str, str]) -> str:
    text = _MENTION.sub(lambda match: f"@{users.get(match.group(1), 'user')}", text)
    text = _CHANNEL.sub(lambda match: f"#{channels.get(match.group(1), 'channel')}", text)
    return _EMOJI.sub(lambda match: f":{match.group(1)}:", text)


def _discord_messages(payload: Any) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, str]]:
    if isinstance(payload, list):
        return payload, {}, {}
    if not isinstance(payload, dict):
        return [], {}, {}
    messages = payload.get("messages", payload.get("Messages", []))
    users = payload.get("users", payload.get("Users", []))
    channels = payload.get("channels", payload.get("Channels", []))
    user_lookup = {
        str(item.get("id", item.get("Id"))): str(item.get("name", item.get("username", item.get("Name", "user"))))
        for item in users if isinstance(item, dict)
    }
    channel_lookup = {
        str(item.get("id", item.get("Id"))): str(item.get("name", item.get("Name", "channel")))
        for item in channels if isinstance(item, dict)
    }
    return messages if isinstance(messages, list) else [], user_lookup, channel_lookup


def parse_discord(path: Path) -> Iterator[RawUnit]:
    """Parse DiscordChatExporter JSON or a lightweight timestamped TXT export."""
    if path.suffix.casefold() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        messages, users, channels = _discord_messages(payload)
        for ordinal, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            author = message.get("author", message.get("Author", {})) or {}
            author_name = str(author.get("name", author.get("username", author.get("Name", "unknown"))))
            if author.get("isBot") or author.get("bot") or _BOT_NAME.search(author_name):
                continue
            kind = str(message.get("type", message.get("Type", "Default")))
            if kind.casefold() not in {"default", "reply", "0", "19"}:
                continue
            content = _rewrite_discord(str(message.get("content", message.get("Content", ""))), users, channels)
            content = normalize_text(content)
            if len(content) < 3 or _URL_ONLY.fullmatch(content):
                continue
            timestamp = _parse_datetime(message.get("timestamp", message.get("Timestamp")))
            channel = str(message.get("channel", message.get("channelName", path.stem)))
            reply = message.get("reference", message.get("replyTo"))
            yield RawUnit(content, author_name, timestamp, ordinal, {"channel": channel, "reply_to": reply})
        return

    for ordinal, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        match = re.match(r"(?:\[(?P<time>[^]]+)\]\s*)?(?P<speaker>[^:]{1,80}):\s*(?P<text>.*)", line)
        if not match:
            continue
        speaker = match.group("speaker").strip()
        content = normalize_text(match.group("text"))
        if _BOT_NAME.search(speaker) or len(content) < 3 or _URL_ONLY.fullmatch(content):
            continue
        yield RawUnit(content, speaker, _parse_datetime(match.group("time")), ordinal, {"channel": path.stem})


def parse_transcript(path: Path) -> Iterator[RawUnit]:
    """Parse JSON segments or Speaker: text transcript exports and merge speaker turns."""
    if path.suffix.casefold() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        segments = payload.get("segments", payload) if isinstance(payload, dict) else payload
        meeting = str(payload.get("meeting", path.stem)) if isinstance(payload, dict) else path.stem
    else:
        segments = []
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(
                r"(?:\[(?P<time>[^]]+)\]\s*)?(?P<speaker>[^:]{1,80}):\s*(?P<text>.*)", line
            )
            if match:
                segments.append(
                    {
                        "speaker": match.group("speaker").strip(),
                        "timestamp": match.group("time"),
                        "text": match.group("text"),
                    }
                )
            else:
                segments.append({"text": line})
        meeting = path.stem
    if not isinstance(segments, list):
        return
    section: str | None = None
    pending_speaker: str | None = None
    pending_text: list[str] = []
    pending_time: datetime | None = None
    ordinal = 0

    def flush() -> RawUnit | None:
        nonlocal ordinal, pending_speaker, pending_text, pending_time
        if not pending_text:
            return None
        unit = RawUnit(" ".join(pending_text), pending_speaker, pending_time, ordinal, {"meeting": meeting, "section": section})
        ordinal += 1
        pending_speaker, pending_text, pending_time = None, [], None
        return unit

    for segment in segments:
        if not isinstance(segment, dict):
            continue
        raw = str(segment.get("text", segment.get("content", "")))
        heading = raw.strip().rstrip(":")
        if heading.startswith("#") or re.fullmatch(r"(?:agenda|topic|section)\s*[:\-].+", heading, re.IGNORECASE):
            flushed = flush()
            if flushed:
                yield flushed
            section = heading.lstrip("#").strip()
            continue
        raw = _TIMESTAMP_GUTTER.sub(" ", raw)
        text = normalize_text(raw)
        if not text or _FILLER.fullmatch(text):
            continue
        speaker = str(segment.get("speaker", segment.get("name", "Unknown"))).strip()
        timestamp = _parse_datetime(segment.get("timestamp", segment.get("start")))
        if pending_speaker and speaker != pending_speaker:
            flushed = flush()
            if flushed:
                yield flushed
        if not pending_speaker:
            pending_speaker, pending_time = speaker, timestamp
        pending_text.append(text)
    flushed = flush()
    if flushed:
        yield flushed


def parse_policy_doc(path: Path) -> Iterator[RawUnit]:
    """Parse policy documents into paragraph units carrying byte-compatible section names."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    blocks = _section_blocks(text) or [(path.stem, 1, len(lines))]
    ordinal = 0
    for section, start, end in blocks:
        content = "\n".join(lines[start - 1 : end]).strip()
        for paragraph in re.split(r"\n\s*\n", content):
            normalized = normalize_text(paragraph)
            if not normalized:
                continue
            yield RawUnit(normalized, None, None, ordinal, {"section": section, "boundary": ordinal == 0 or paragraph == content})
            ordinal += 1


def parse_by_type(path: Path) -> Iterator[RawUnit]:
    """Choose a parser from filename/source-directory conventions."""
    lowered = path.name.casefold()
    if "discord" in lowered or path.parent.name.casefold() == "discord":
        yield from parse_discord(path)
    elif "transcript" in lowered or path.parent.name.casefold() in {"transcripts", "meetings"}:
        yield from parse_transcript(path)
    else:
        yield from parse_policy_doc(path)
