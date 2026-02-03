"""Tests for CLI argument parsing."""

from podclaw.cli import _parse_duration


class TestParseDuration:
    def test_seconds(self):
        assert _parse_duration("90s") == 90
        assert _parse_duration("30s") == 30

    def test_minutes(self):
        assert _parse_duration("2m") == 120
        assert _parse_duration("5m") == 300

    def test_combined(self):
        assert _parse_duration("1m30s") == 90
        assert _parse_duration("2m15s") == 135

    def test_raw_number(self):
        assert _parse_duration("60") == 60

    def test_whitespace(self):
        assert _parse_duration("  2m  ") == 120
