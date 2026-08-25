"""Offline tests for source cleaning and deterministic chunk boundaries."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from benchmark_cli.ingestion.chunk import chunk_units, token_count
from benchmark_cli.ingestion.clean import RawUnit, normalize_text, parse_discord, parse_transcript


def unit(text: str, ordinal: int, **extra: object) -> RawUnit:
    return RawUnit(text=text, speaker="A", timestamp=datetime(2026, 1, 1, 9) + timedelta(minutes=ordinal), ordinal=ordinal, extra=extra)


@pytest.mark.unit
class ChunkingTests(unittest.TestCase):
    def test_normalization_redacts_secrets_and_keeps_code_fences(self) -> None:
        text = "Password=topsecret\n\n```\nvalue    =  1\n```\n\u201cquoted\u201d"
        cleaned = normalize_text(text)
        self.assertIn("[REDACTED]", cleaned)
        self.assertNotIn("topsecret", cleaned)
        self.assertIn("value    =  1", cleaned)
        self.assertIn('"quoted"', cleaned)

    def test_does_not_cross_section_or_channel_boundaries(self) -> None:
        units = [
            unit("one " * 40, 0, section="First", boundary=True),
            unit("two " * 40, 1, section="First"),
            unit("three " * 40, 2, section="Second", boundary=True),
        ]
        chunks = chunk_units(units, target_tokens=70, max_tokens=100, min_tokens=10, overlap_tokens=5)
        self.assertGreaterEqual(len(chunks), 2)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 100)
            self.assertEqual(len({item.extra["section"] for item in chunk.units}), 1)

    def test_splits_a_single_oversize_unit(self) -> None:
        chunks = chunk_units([unit("Sentence. " * 250, 0, section="Long", boundary=True)], max_tokens=100, target_tokens=80, min_tokens=10)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.split_unit for chunk in chunks))
        self.assertTrue(all(chunk.token_count <= 100 for chunk in chunks))
        self.assertGreater(token_count(chunks[0].text), 0)

    def test_discord_parser_filters_noise_and_rewrites_mentions(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "discord_export.json"
            path.write_text(
                '{"users":[{"id":"1","name":"Alice"}],"channels":[{"id":"2","name":"eng"}],'
                '"messages":[{"author":{"name":"Build Bot","isBot":true},"content":"ignore"},'
                '{"author":{"name":"Alice"},"content":"<@1> see <#2> <a:shipit:3> password=secret",'
                '"timestamp":"2026-01-01T10:00:00Z"}]}',
                encoding="utf-8",
            )
            units = list(parse_discord(path))
        self.assertEqual(len(units), 1)
        self.assertIn("@Alice", units[0].text)
        self.assertIn("#eng", units[0].text)
        self.assertIn(":shipit:", units[0].text)
        self.assertIn("[REDACTED]", units[0].text)

    def test_transcript_parser_merges_consecutive_speaker_turns(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "transcript.txt"
            path.write_text("# Agenda\n[00:00:01] Alice: First point\nAlice: Second point\nBob: Reply", encoding="utf-8")
            units = list(parse_transcript(path))
        self.assertEqual(len(units), 2)
        self.assertEqual(units[0].speaker, "Alice")
        self.assertIn("First point Second point", units[0].text)
        self.assertEqual(units[0].extra["section"], "Agenda")


if __name__ == "__main__":
    unittest.main()
