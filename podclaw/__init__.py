"""
PodClaw - One-prompt podcast production tool.

Generate full podcast episodes (script → TTS → video) from a single topic prompt.
"""

__version__ = "0.1.0"
__author__ = "v0id_injector"

from podclaw.generator import PodcastGenerator
from podclaw.config import PodclawConfig, Voice, Format

__all__ = ["PodcastGenerator", "PodclawConfig", "Voice", "Format"]
