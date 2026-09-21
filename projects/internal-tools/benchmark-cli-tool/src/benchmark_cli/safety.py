"""Safety boundaries for content retrieved from user-managed documents."""

from __future__ import annotations

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
