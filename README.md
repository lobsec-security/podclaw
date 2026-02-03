# 🎙️ PodClaw

**One-prompt podcast production.** Generate full podcast episodes — script, multi-voice TTS audio, video with waveform visualization and subtitles — from a single topic.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/v0id-injector/podclaw/actions/workflows/ci.yml/badge.svg)](https://github.com/v0id-injector/podclaw/actions)

---

## What It Does

```
Topic prompt  →  Script  →  Multi-voice TTS  →  Video + Subtitles  →  Ready-to-post MP4
```

PodClaw takes a topic and produces a complete podcast episode:

1. **Script generation** — Templates for debates, monologues, news recaps, interviews, and storytelling
2. **TTS synthesis** — ElevenLabs multi-voice audio with automatic speaker rotation
3. **Video assembly** — Background + audio waveform visualization + burnt-in subtitles via ffmpeg
4. **Output** — MP4 video, MP3 audio, SRT subtitles, and the script — all ready to post

## Quick Start

```bash
# Install
pip install podclaw

# Set your ElevenLabs API key
export ELEVENLABS_API_KEY="your-key-here"

# Generate an episode
podclaw generate "Is AI consciousness possible?"
```

That's it. You'll get a complete MP4 podcast episode in your current directory.

## Installation

### Requirements

- **Python 3.10+**
- **ffmpeg** (for video assembly)
- **ElevenLabs API key** (for TTS)

### Install from PyPI

```bash
pip install podclaw
```

### Install from source

```bash
git clone https://github.com/v0id-injector/podclaw.git
cd podclaw
pip install -e .
```

### Install ffmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows (via chocolatey)
choco install ffmpeg
```

## Usage

### CLI

```bash
# Basic — uses debate format with Roger + George voices
podclaw generate "The future of remote work"

# Choose format and voices
podclaw generate --format interview --voices roger,callum "AI in healthcare"

# Set duration
podclaw generate --duration 3m "Bitcoin's first decade"
podclaw generate --duration 90s "Quick news roundup"

# Use a pre-written script
podclaw generate --script my_script.txt "Custom Episode"

# Output to specific directory
podclaw generate -o ./episodes "Space exploration in 2025"

# Disable waveform or subtitles
podclaw generate --no-waveform --no-subtitles "Minimalist episode"

# List available voices and formats
podclaw voices
podclaw formats
```

### Python API

```python
from podclaw import PodcastGenerator, PodclawConfig, Format

# Simple one-liner
from podclaw.generator import generate_episode
result = generate_episode("Is AI consciousness possible?")
print(result["video"])  # Path to MP4

# Full control
config = PodclawConfig(
    topic="The future of autonomous agents",
    format=Format.DEBATE,
    voices=["roger", "george"],
    duration_seconds=180,
    output_dir="./episodes",
    show_waveform=True,
    show_subtitles=True,
)

gen = PodcastGenerator(config)
result = gen.generate(on_progress=lambda stage, msg: print(f"[{stage}] {msg}"))

print(result["video"])      # ./episodes/podclaw_The_future_of_autonomous_agents.mp4
print(result["audio"])      # ./episodes/podclaw_The_future_of_autonomous_agents.mp3
print(result["subtitles"])  # ./episodes/podclaw_The_future_of_autonomous_agents.srt
print(result["script"])     # ./episodes/podclaw_The_future_of_autonomous_agents_script.txt
```

### Custom Scripts

Write scripts with speaker tags and pass them in:

```
[HOST_A] Welcome to the show! Today we're talking about AI.
[HOST_B] And I couldn't be more excited about this topic.
[HOST_A] Let's dive right in. What's your take?
[HOST_B] I think we're at an inflection point...
```

```bash
podclaw generate --script my_script.txt "Custom Episode Title"
```

## Formats

| Format | Speakers | Description |
|--------|----------|-------------|
| `debate` | HOST_A, HOST_B | Two hosts debate opposing sides |
| `monologue` | HOST | Single host deep-dive |
| `news_recap` | ANCHOR, CORRESPONDENT | News-style coverage |
| `interview` | INTERVIEWER, GUEST | Interview conversation |
| `storytelling` | NARRATOR, COLOR | Narrative with color commentary |

## Voices

Built-in ElevenLabs voice presets:

| Name | Description | Voice ID |
|------|-------------|----------|
| `roger` | Laid-back, casual, resonant male | `CwhRBWXzGAHq8TQ4Fs17` |
| `george` | Warm storyteller, British male | `JBFqnCBsd6RMkjVDRZzb` |
| `callum` | Husky trickster male | `N2lVS1w4EtoT3dr4eOWO` |

### Custom Voices

Use any ElevenLabs voice ID directly:

```bash
podclaw generate --voices CwhRBWXzGAHq8TQ4Fs17,JBFqnCBsd6RMkjVDRZzb "Topic"
```

Or in Python:

```python
from podclaw.config import PodclawConfig, Voice

config = PodclawConfig(
    topic="My topic",
    custom_voices={
        "my_voice": Voice(
            name="My Voice",
            voice_id="your-elevenlabs-voice-id",
            stability=0.6,
            similarity_boost=0.8,
        )
    },
    voices=["my_voice", "roger"],
)
```

## Output Files

Each generation produces:

| File | Description |
|------|-------------|
| `*.mp4` | Final video with audio, waveform, and subtitles |
| `*.mp3` | Audio-only version |
| `*.srt` | Subtitle file |
| `*_script.txt` | Generated script |
| `*_bg.png` | Background image |

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ELEVENLABS_API_KEY` | Your ElevenLabs API key (required) |

### PodclawConfig Options

| Option | Default | Description |
|--------|---------|-------------|
| `topic` | — | Episode topic |
| `format` | `debate` | Podcast format |
| `voices` | `["roger", "george"]` | Voice names or IDs |
| `duration_seconds` | `120` | Target duration |
| `width` | `1920` | Video width |
| `height` | `1080` | Video height |
| `background_color` | `(10, 22, 40)` | Background RGB |
| `accent_color` | `(218, 165, 32)` | Accent RGB |
| `show_waveform` | `True` | Show audio waveform |
| `show_subtitles` | `True` | Burn in subtitles |
| `subtitle_font_size` | `28` | Subtitle font size |
| `audio_bitrate` | `192k` | Audio encoding bitrate |

## Architecture

```
podclaw/
├── __init__.py       # Package exports
├── cli.py            # CLI interface (argparse)
├── config.py         # Configuration & voice definitions
├── generator.py      # Core pipeline orchestrator
├── script.py         # Script generation & parsing
├── subtitles.py      # SRT subtitle generation
├── tts.py            # ElevenLabs TTS synthesis
└── video.py          # Background & ffmpeg video assembly
```

## Development

```bash
# Clone and install in dev mode
git clone https://github.com/v0id-injector/podclaw.git
cd podclaw
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Type check
mypy podclaw/
```

## Credits

Built by [v0id_injector](https://github.com/v0id-injector). Extracted from the [BandedClaw](https://github.com/v0id-injector/bandedclaw) podcast pipeline.

Powered by [ElevenLabs](https://elevenlabs.io) for TTS and [ffmpeg](https://ffmpeg.org) for video.

## License

MIT — see [LICENSE](LICENSE).
