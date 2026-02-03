"""Tests for configuration."""

import pytest
from podclaw.config import PodclawConfig, Voice, Format, VOICES


class TestVoiceResolution:
    def test_builtin_voices(self):
        config = PodclawConfig()
        voice = config.get_voice("roger")
        assert voice.name == "Roger"
        assert voice.voice_id == "CwhRBWXzGAHq8TQ4Fs17"

    def test_case_insensitive(self):
        config = PodclawConfig()
        voice = config.get_voice("ROGER")
        assert voice.name == "Roger"

    def test_custom_voice(self):
        config = PodclawConfig(
            custom_voices={
                "myvoice": Voice(name="My Voice", voice_id="abc123")
            }
        )
        voice = config.get_voice("myvoice")
        assert voice.voice_id == "abc123"

    def test_raw_voice_id_fallback(self):
        config = PodclawConfig()
        voice = config.get_voice("some_random_id_123")
        assert voice.voice_id == "some_random_id_123"

    def test_get_all_voices(self):
        config = PodclawConfig(voices=["roger", "george", "callum"])
        voices = config.get_all_voices()
        assert len(voices) == 3
        assert voices[0].name == "Roger"
        assert voices[1].name == "George"
        assert voices[2].name == "Callum"


class TestBuiltinVoices:
    def test_all_voices_have_ids(self):
        for name, voice in VOICES.items():
            assert voice.voice_id, f"{name} has no voice_id"
            assert voice.name, f"{name} has no name"

    def test_expected_voices_exist(self):
        assert "roger" in VOICES
        assert "george" in VOICES
        assert "callum" in VOICES


class TestFormat:
    def test_all_formats(self):
        assert len(Format) == 5
        assert Format.DEBATE.value == "debate"
        assert Format.MONOLOGUE.value == "monologue"
