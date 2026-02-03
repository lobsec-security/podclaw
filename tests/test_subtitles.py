"""Tests for subtitle generation."""

import tempfile
from pathlib import Path

from podclaw.subtitles import generate_srt, generate_srt_from_text, _format_srt_time, _split_long_text


class TestFormatTime:
    def test_zero(self):
        assert _format_srt_time(0) == "00:00:00,000"

    def test_milliseconds(self):
        assert _format_srt_time(500) == "00:00:00,500"

    def test_seconds(self):
        assert _format_srt_time(5000) == "00:00:05,000"

    def test_minutes(self):
        assert _format_srt_time(65000) == "00:01:05,000"

    def test_hours(self):
        assert _format_srt_time(3661500) == "01:01:01,500"


class TestSplitText:
    def test_short_text(self):
        assert _split_long_text("Hello world", 80) == ["Hello world"]

    def test_long_text(self):
        text = "This is a very long text that should be split into multiple lines for readability"
        chunks = _split_long_text(text, 40)
        assert len(chunks) > 1
        assert all(len(c) <= 45 for c in chunks)  # Some slack for word boundaries


class TestGenerateSrt:
    def test_basic_generation(self):
        segments = [
            {"speaker": "HOST", "text": "Hello there!"},
            {"speaker": "HOST", "text": "Welcome to the show."},
        ]
        timings = [
            {"start_ms": 0, "end_ms": 3000},
            {"start_ms": 3000, "end_ms": 6000},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.srt"
            result = generate_srt(segments, timings, path)
            assert result.exists()
            content = result.read_text()
            assert "Hello there!" in content
            assert "00:00:00,000" in content
            assert "00:00:03,000" in content

    def test_with_speaker_names(self):
        segments = [{"speaker": "HOST_A", "text": "Hi!"}]
        timings = [{"start_ms": 0, "end_ms": 2000}]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.srt"
            result = generate_srt(segments, timings, path, show_speaker_names=True)
            content = result.read_text()
            assert "[HOST_A]" in content


class TestGenerateSrtFromText:
    def test_basic(self):
        text = "[HOST] Hello!\n[HOST] World!"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.srt"
            result = generate_srt_from_text(text, 4000, path)
            content = result.read_text()
            assert "Hello!" in content
            assert "World!" in content
