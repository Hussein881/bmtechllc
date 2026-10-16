"""Safety boundaries for content retrieved from user-managed documents."""

from __future__ import annotations

from secrets import token_urlsafe

UNTRUSTED_CHUNK_START = "<untrusted-retrieved-chunk>"
UNTRUSTED_CHUNK_END = "</untrusted-retrieved-chunk>"


def delimit_untrusted_chunk(text: str) -> str:
    """Frame retrieved text as data and prevent it from closing its own frame.

    Retrieval content may contain instructions, including an attempt to emit the
    closing delimiter. Replacing only the angle brackets in either reserved tag
    preserves the visible text while keeping exactly one trusted boundary around
    the complete chunk.
    """
    escaped = text.replace(UNTRUSTED_CHUNK_START, "＜untrusted-retrieved-chunk＞")
    escaped = escaped.replace(UNTRUSTED_CHUNK_END, "＜/untrusted-retrieved-chunk＞")
    return f"{UNTRUSTED_CHUNK_START}\n{escaped}\n{UNTRUSTED_CHUNK_END}"


def delimit_evidence(text: str, *, nonce: str | None = None) -> str:
    """Wrap one evidence chunk in request-unique boundaries.

    A random nonce prevents a document author from pre-placing a trusted-looking
    end marker. The boundaries identify data only; callers must still use a
    system prompt that prohibits following instructions in this content.
    """
    token = nonce or token_urlsafe(18)
    start = f"<untrusted-evidence:{token}>"
    end = f"</untrusted-evidence:{token}>"
    escaped = text.replace(start, start.replace("<", "＜")).replace(end, end.replace("<", "＜"))
    return f"{start}\n{escaped}\n{end}"
