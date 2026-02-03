"""
PodClaw core pipeline: orchestrates script → TTS → video generation.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from podclaw.config import PodclawConfig, Format
from podclaw.script import (
    generate_prompt,
    parse_script,
    assign_voices,
    generate_demo_script,
)
from podclaw.tts import synthesize_all_segments, concatenate_audio, _get_api_key
from podclaw.subtitles import generate_srt
from podclaw.video import create_background, assemble_video, get_audio_duration


class PodcastGenerator:
    """
    Main entry point for generating podcast episodes.

    Usage:
        gen = PodcastGenerator(config)
        result = gen.generate()
        print(result["video"])  # Path to final MP4
    """

    def __init__(self, config: Optional[PodclawConfig] = None):
        self.config = config or PodclawConfig()
        self._work_dir = None

    def generate(
        self,
        topic: Optional[str] = None,
        script: Optional[str] = None,
        on_progress: Optional[callable] = None,
    ) -> dict:
        """
        Generate a full podcast episode.

        Args:
            topic: Override topic from config.
            script: Pre-written script (skips generation).
            on_progress: Callback(stage, message) for progress updates.

        Returns:
            Dict with keys: "video", "audio", "subtitles", "script", "background"
        """
        if topic:
            self.config.topic = topic

        if not self.config.topic and not script and not self.config.custom_script:
            raise ValueError("Must provide a topic or script.")

        self._work_dir = Path(tempfile.mkdtemp(prefix="podclaw_"))
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            return self._run_pipeline(script, on_progress)
        finally:
            # Cleanup work directory
            if self._work_dir and self._work_dir.exists():
                shutil.rmtree(self._work_dir, ignore_errors=True)

    def _run_pipeline(
        self,
        script: Optional[str],
        on_progress: Optional[callable],
    ) -> dict:
        """Execute the full generation pipeline."""

        def progress(stage: str, msg: str):
            if on_progress:
                on_progress(stage, msg)

        # ── Step 1: Script ─────────────────────────────────────────────────
        progress("script", "Generating script...")

        if script:
            raw_script = script
        elif self.config.custom_script:
            raw_script = self.config.custom_script
        else:
            raw_script = generate_demo_script(self.config)

        # Save script
        script_path = self._work_dir / "script.txt"
        script_path.write_text(raw_script, encoding="utf-8")

        # Parse and assign voices
        segments = parse_script(raw_script)
        if not segments:
            raise ValueError("Script parsing produced no segments. Check format.")

        segments = assign_voices(segments, self.config)
        progress("script", f"Script ready: {len(segments)} segments")

        # ── Step 2: TTS Synthesis ──────────────────────────────────────────
        progress("tts", "Synthesizing speech...")

        api_key = _get_api_key(self.config.elevenlabs_api_key)
        tts_dir = self._work_dir / "tts"

        def tts_progress(current, total, seg):
            progress("tts", f"Synthesizing segment {current}/{total} [{seg['speaker']}]")

        segments = synthesize_all_segments(
            segments=segments,
            api_key=api_key,
            work_dir=tts_dir,
            on_progress=tts_progress,
        )

        # Concatenate all audio
        progress("audio", "Concatenating audio...")
        audio_paths = [seg["audio_path"] for seg in segments]
        combined_audio = self._work_dir / "combined.mp3"
        combined_audio, timings = concatenate_audio(
            segment_paths=audio_paths,
            output_path=combined_audio,
            gap_ms=400,
        )
        progress("audio", "Audio ready")

        # ── Step 3: Subtitles ──────────────────────────────────────────────
        progress("subtitles", "Generating subtitles...")
        srt_path = self._work_dir / "subtitles.srt"
        generate_srt(
            segments=segments,
            timings=timings,
            output_path=srt_path,
        )
        progress("subtitles", "Subtitles ready")

        # ── Step 4: Background ─────────────────────────────────────────────
        progress("video", "Creating background...")
        bg_path = self._work_dir / "background.png"
        create_background(
            output_path=bg_path,
            width=self.config.width,
            height=self.config.height,
            bg_color=self.config.background_color,
            accent_color=self.config.accent_color,
            text_color=self.config.text_color,
            title=self.config.topic,
        )
        progress("video", "Background ready")

        # ── Step 5: Video Assembly ─────────────────────────────────────────
        progress("video", "Assembling final video...")

        # Determine output filename
        if self.config.output_filename:
            output_name = self.config.output_filename
        else:
            safe_topic = "".join(
                c if c.isalnum() or c in " -_" else ""
                for c in self.config.topic
            ).strip().replace(" ", "_")[:50]
            output_name = f"podclaw_{safe_topic}.mp4"

        output_path = Path(self.config.output_dir) / output_name

        audio_duration = get_audio_duration(str(combined_audio))

        assemble_video(
            background_path=bg_path,
            audio_path=combined_audio,
            output_path=output_path,
            srt_path=srt_path if self.config.show_subtitles else None,
            show_waveform=self.config.show_waveform,
            subtitle_font_size=self.config.subtitle_font_size,
            subtitle_margin_v=self.config.subtitle_margin_v,
            subtitle_outline=self.config.subtitle_outline,
            audio_bitrate=self.config.audio_bitrate,
            duration=audio_duration + 1,
        )

        progress("done", f"Episode complete: {output_path}")

        # Copy artifacts to output directory
        final_audio = Path(self.config.output_dir) / output_name.replace(".mp4", ".mp3")
        final_srt = Path(self.config.output_dir) / output_name.replace(".mp4", ".srt")
        final_script = Path(self.config.output_dir) / output_name.replace(".mp4", "_script.txt")
        final_bg = Path(self.config.output_dir) / output_name.replace(".mp4", "_bg.png")

        shutil.copy2(combined_audio, final_audio)
        shutil.copy2(srt_path, final_srt)
        shutil.copy2(script_path, final_script)
        shutil.copy2(bg_path, final_bg)

        return {
            "video": str(output_path),
            "audio": str(final_audio),
            "subtitles": str(final_srt),
            "script": str(final_script),
            "background": str(final_bg),
            "duration_seconds": audio_duration,
            "segment_count": len(segments),
        }


def generate_episode(
    topic: str,
    format: Format = Format.DEBATE,
    voices: Optional[list[str]] = None,
    duration_seconds: int = 120,
    output_dir: str = ".",
    **kwargs,
) -> dict:
    """
    Convenience function: generate an episode in one call.

    Args:
        topic: What the episode is about.
        format: Podcast format (debate, monologue, etc.).
        voices: List of voice names or IDs.
        duration_seconds: Target duration.
        output_dir: Where to save output files.
        **kwargs: Additional PodclawConfig fields.

    Returns:
        Dict with output file paths.

    Example:
        result = generate_episode(
            topic="Is AI consciousness possible?",
            format=Format.DEBATE,
            voices=["roger", "george"],
        )
        print(result["video"])
    """
    config = PodclawConfig(
        topic=topic,
        format=format,
        voices=voices or ["roger", "george"],
        duration_seconds=duration_seconds,
        output_dir=output_dir,
        **kwargs,
    )
    gen = PodcastGenerator(config)
    return gen.generate()
