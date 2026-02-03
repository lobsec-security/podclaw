"""
PodClaw configuration and voice definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Format(str, Enum):
    """Podcast format templates."""
    DEBATE = "debate"
    MONOLOGUE = "monologue"
    NEWS_RECAP = "news_recap"
    INTERVIEW = "interview"
    STORYTELLING = "storytelling"


@dataclass
class Voice:
    """ElevenLabs voice configuration."""
    name: str
    voice_id: str
    description: str = ""
    model_id: str = "eleven_multilingual_v2"
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True


# Built-in voice presets
VOICES = {
    "roger": Voice(
        name="Roger",
        voice_id="CwhRBWXzGAHq8TQ4Fs17",
        description="Laid-back, casual, resonant male",
    ),
    "george": Voice(
        name="George",
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        description="Warm storyteller, British male",
    ),
    "callum": Voice(
        name="Callum",
        voice_id="N2lVS1w4EtoT3dr4eOWO",
        description="Husky trickster male",
    ),
}


@dataclass
class PodclawConfig:
    """Full configuration for a podcast episode generation."""

    # Content
    topic: str = ""
    format: Format = Format.DEBATE
    duration_seconds: int = 120
    custom_script: Optional[str] = None

    # Voices
    voices: List[str] = field(default_factory=lambda: ["roger", "george"])
    custom_voices: Dict[str, Voice] = field(default_factory=dict)

    # Video
    width: int = 1920
    height: int = 1080
    background_color: Tuple[int, int, int] = (10, 22, 40)
    accent_color: Tuple[int, int, int] = (218, 165, 32)
    text_color: Tuple[int, int, int] = (255, 253, 240)
    show_waveform: bool = True
    show_subtitles: bool = True

    # Subtitle styling
    subtitle_font_size: int = 28
    subtitle_margin_v: int = 60
    subtitle_outline: int = 3

    # Output
    output_dir: str = "."
    output_filename: Optional[str] = None

    # TTS
    elevenlabs_api_key: Optional[str] = None
    tts_model: str = "eleven_multilingual_v2"

    # Audio
    audio_bitrate: str = "192k"

    def get_voice(self, name: str) -> Voice:
        """Resolve a voice name to a Voice object."""
        name_lower = name.lower()
        if name_lower in self.custom_voices:
            return self.custom_voices[name_lower]
        if name_lower in VOICES:
            return VOICES[name_lower]
        # Treat as a raw ElevenLabs voice ID
        return Voice(name=name, voice_id=name, description="Custom voice ID")

    def get_all_voices(self) -> List[Voice]:
        """Get all configured voices as Voice objects."""
        return [self.get_voice(v) for v in self.voices]
