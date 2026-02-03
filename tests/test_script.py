"""Tests for script generation and parsing."""

import pytest
from podclaw.config import PodclawConfig, Format, VOICES
from podclaw.script import (
    parse_script,
    assign_voices,
    generate_demo_script,
    generate_prompt,
    estimate_word_count,
    format_duration,
    SPEAKER_ROLES,
)


class TestParseScript:
    def test_basic_parsing(self):
        script = """[HOST_A] Hello there!
[HOST_B] Welcome to the show.
[HOST_A] Let's get started."""
        segments = parse_script(script)
        assert len(segments) == 3
        assert segments[0]["speaker"] == "HOST_A"
        assert segments[0]["text"] == "Hello there!"
        assert segments[1]["speaker"] == "HOST_B"
        assert segments[2]["speaker"] == "HOST_A"

    def test_multiline_text(self):
        script = """[HOST] This is the first line.
And this continues on the next line.
[HOST] New segment."""
        segments = parse_script(script)
        assert len(segments) == 2
        assert "first line. And this continues" in segments[0]["text"]

    def test_empty_script(self):
        assert parse_script("") == []
        assert parse_script("   \n\n  ") == []

    def test_no_tags(self):
        assert parse_script("Just some text without tags") == []


class TestAssignVoices:
    def test_voice_assignment(self):
        segments = [
            {"speaker": "HOST_A", "text": "Hello"},
            {"speaker": "HOST_B", "text": "Hi"},
            {"speaker": "HOST_A", "text": "Let's go"},
        ]
        config = PodclawConfig(voices=["roger", "george"])
        result = assign_voices(segments, config)

        assert result[0]["voice"].name == "Roger"
        assert result[1]["voice"].name == "George"
        assert result[2]["voice"].name == "Roger"  # Same speaker = same voice

    def test_single_voice_wraps(self):
        segments = [
            {"speaker": "A", "text": "One"},
            {"speaker": "B", "text": "Two"},
            {"speaker": "C", "text": "Three"},
        ]
        config = PodclawConfig(voices=["roger"])
        result = assign_voices(segments, config)
        # All should get roger since there's only one voice
        assert all(r["voice"].name == "Roger" for r in result)


class TestDemoScript:
    @pytest.mark.parametrize("fmt", list(Format))
    def test_generates_for_all_formats(self, fmt):
        config = PodclawConfig(topic="Test topic", format=fmt)
        script = generate_demo_script(config)
        assert len(script) > 0
        assert "[" in script  # Has speaker tags

    def test_topic_appears_in_script(self):
        config = PodclawConfig(topic="quantum computing", format=Format.DEBATE)
        script = generate_demo_script(config)
        assert "quantum computing" in script.lower()


class TestPromptGeneration:
    def test_prompt_includes_topic(self):
        config = PodclawConfig(topic="AI safety", format=Format.DEBATE)
        prompt = generate_prompt(config)
        assert "AI safety" in prompt

    def test_prompt_includes_word_count(self):
        config = PodclawConfig(topic="test", duration_seconds=120)
        prompt = generate_prompt(config)
        assert "300" in prompt  # ~150 wpm * 2 min


class TestHelpers:
    def test_word_count_estimate(self):
        assert estimate_word_count(60) == 150
        assert estimate_word_count(120) == 300

    def test_format_duration(self):
        assert format_duration(30) == "30 seconds"
        assert format_duration(60) == "1 minute"
        assert format_duration(120) == "2 minutes"
        assert format_duration(90) == "1m 30s"

    def test_all_formats_have_roles(self):
        for fmt in Format:
            assert fmt in SPEAKER_ROLES
