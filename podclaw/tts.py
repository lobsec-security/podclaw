"""
Text-to-speech synthesis via ElevenLabs API.

Handles voice synthesis, audio concatenation, and timing extraction.
"""

import io
import os
import struct
import tempfile
import wave
from pathlib import Path
from typing import Optional

from podclaw.config import Voice


def _get_api_key(config_key: Optional[str] = None) -> str:
    """Resolve the ElevenLabs API key."""
    key = config_key or os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise ValueError(
            "ElevenLabs API key not found. "
            "Set ELEVENLABS_API_KEY environment variable or pass it in config."
        )
    return key


def synthesize_segment(
    text: str,
    voice: Voice,
    api_key: str,
    output_path: Path,
) -> Path:
    """
    Synthesize a single text segment to an MP3 file.

    Args:
        text: The text to synthesize.
        voice: Voice configuration.
        api_key: ElevenLabs API key.
        output_path: Where to save the MP3 file.

    Returns:
        Path to the generated MP3 file.
    """
    import requests

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice.voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }

    payload = {
        "text": text,
        "model_id": voice.model_id,
        "voice_settings": {
            "stability": voice.stability,
            "similarity_boost": voice.similarity_boost,
            "style": voice.style,
            "use_speaker_boost": voice.use_speaker_boost,
        },
    }

    response = requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path


def synthesize_all_segments(
    segments: list[dict],
    api_key: str,
    work_dir: Path,
    on_progress: Optional[callable] = None,
) -> list[dict]:
    """
    Synthesize all script segments to individual audio files.

    Args:
        segments: List of {"speaker", "text", "voice"} dicts.
        api_key: ElevenLabs API key.
        work_dir: Working directory for temporary files.
        on_progress: Optional callback(current, total, segment).

    Returns:
        Segments with added "audio_path" key.
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, seg in enumerate(segments):
        audio_path = work_dir / f"segment_{i:04d}.mp3"

        if on_progress:
            on_progress(i + 1, len(segments), seg)

        synthesize_segment(
            text=seg["text"],
            voice=seg["voice"],
            api_key=api_key,
            output_path=audio_path,
        )

        results.append({**seg, "audio_path": str(audio_path)})

    return results


def concatenate_audio(
    segment_paths: list[str],
    output_path: Path,
    gap_ms: int = 300,
) -> tuple[Path, list[dict]]:
    """
    Concatenate audio segments into a single file with gaps between segments.
    Uses ffmpeg for reliable MP3 handling.

    Args:
        segment_paths: List of paths to MP3 files.
        output_path: Where to save the concatenated audio.
        gap_ms: Milliseconds of silence between segments.

    Returns:
        Tuple of (output_path, timing_info) where timing_info is a list of
        {"start_ms", "end_ms", "path"} dicts.
    """
    import subprocess

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get durations of each segment via ffprobe
    timings = []
    current_ms = 0

    for path in segment_paths:
        duration_ms = _get_duration_ms(path)
        timings.append({
            "start_ms": current_ms,
            "end_ms": current_ms + duration_ms,
            "path": path,
        })
        current_ms += duration_ms + gap_ms

    # Build ffmpeg concat filter
    # Create silence file
    silence_path = output_path.parent / "_silence.mp3"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=channel_layout=mono:sample_rate=44100:duration={gap_ms/1000}",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(silence_path),
        ],
        capture_output=True,
        check=True,
    )

    # Build concat list file
    list_path = output_path.parent / "_concat_list.txt"
    with open(list_path, "w") as f:
        for i, path in enumerate(segment_paths):
            f.write(f"file '{path}'\n")
            if i < len(segment_paths) - 1:
                f.write(f"file '{silence_path}'\n")

    # Concatenate
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_path),
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(output_path),
        ],
        capture_output=True,
        check=True,
    )

    # Cleanup temp files
    silence_path.unlink(missing_ok=True)
    list_path.unlink(missing_ok=True)

    return output_path, timings


def _get_duration_ms(audio_path: str) -> int:
    """Get audio duration in milliseconds using ffprobe."""
    import subprocess

    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(float(result.stdout.strip()) * 1000)
