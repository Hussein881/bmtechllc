"""Offline tests for usage-log routing-savings telemetry."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from benchmark_cli.config import get_model_config
from benchmark_cli.telemetry.usage import CSV_FIELDS, log_usage, migrate_usage_log


@pytest.mark.unit
class UsageLogTests(unittest.TestCase):
    def test_migration_backfills_routed_agent_savings(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "usage_log.csv"
            legacy_fields = CSV_FIELDS[:8]
            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=legacy_fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "timestamp": "2026-08-14T00:00:00+00:00",
                        "component": "agent",
                        "question": "test",
                        "tier": "cheap",
                        "model": "gpt-5.6-luna",
                        "prompt_tokens": "1000000",
                        "completion_tokens": "1000000",
                        "total_cost_usd": "1.4000000000",
                    }
                )

            migrate_usage_log(path)
            with path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(tuple(rows[0]), CSV_FIELDS)
            self.assertEqual(rows[0]["flagship_equivalent_cost_usd"], "14.0000000000")
            self.assertEqual(rows[0]["routing_savings_usd"], "12.6000000000")

    def test_new_cheap_agent_row_records_savings(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "usage_log.csv"
            log_usage(
                question="test",
                tier="cheap",
                model_config=get_model_config("cheap"),
                prompt_tokens=100,
                completion_tokens=10,
                log_path=path,
            )
            with path.open(newline="", encoding="utf-8") as file:
                row = next(csv.DictReader(file))

            self.assertGreater(float(row["routing_savings_usd"]), 0.0)
            self.assertGreater(
                float(row["flagship_equivalent_cost_usd"]), float(row["total_cost_usd"])
            )


if __name__ == "__main__":
    unittest.main()
