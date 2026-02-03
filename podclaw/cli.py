"""
PodClaw CLI interface.
"""

import argparse
import sys
import time

from podclaw import __version__
from podclaw.config import PodclawConfig, Format, VOICES
from podclaw.generator import PodcastGenerator


def _parse_duration(s: str) -> int:
    """Parse duration string like '2m', '90s', '1m30s' to seconds."""
    s = s.strip().lower()

    if s.endswith("s") and "m" not in s:
        return int(s[:-1])
    if s.endswith("m") and "s" not in s:
        return int(s[:-1]) * 60

    # Handle '1m30s' format
    total = 0
    if "m" in s:
        parts = s.split("m")
        total += int(parts[0]) * 60
        rest = parts[1]
        if rest.endswith("s"):
            rest = rest[:-1]
        if rest:
            total += int(rest)
    else:
        total = int(s)

    return total


def _progress_callback(stage: str, message: str):
    """Pretty-print progress updates."""
    icons = {
        "script": "📝",
        "tts": "🎙️",
        "audio": "🎵",
        "subtitles": "💬",
        "video": "🎬",
        "done": "✅",
    }
    icon = icons.get(stage, "⏳")
    print(f"  {icon} [{stage}] {message}")


def cmd_generate(args):
    """Handle the 'generate' subcommand."""
    # Parse voices
    voices = [v.strip() for v in args.voices.split(",")] if args.voices else ["roger", "george"]

    # Parse format
    try:
        fmt = Format(args.format)
    except ValueError:
        print(f"❌ Unknown format: {args.format}")
        print(f"   Available: {', '.join(f.value for f in Format)}")
        sys.exit(1)

    # Parse duration
    duration = _parse_duration(args.duration)

    # Build config
    config = PodclawConfig(
        topic=args.topic,
        format=fmt,
        voices=voices,
        duration_seconds=duration,
        output_dir=args.output,
        output_filename=args.filename,
        show_waveform=not args.no_waveform,
        show_subtitles=not args.no_subtitles,
    )

    # Handle custom script
    script = None
    if args.script:
        with open(args.script, "r") as f:
            script = f.read()

    print()
    print("🎙️  PodClaw - Podcast Generator")
    print("=" * 50)
    print(f"  Topic:    {config.topic}")
    print(f"  Format:   {fmt.value}")
    print(f"  Voices:   {', '.join(voices)}")
    print(f"  Duration: {duration}s (~{duration // 60}m {duration % 60}s)")
    print(f"  Output:   {config.output_dir}/")
    print("=" * 50)
    print()

    start = time.time()

    try:
        gen = PodcastGenerator(config)
        result = gen.generate(script=script, on_progress=_progress_callback)
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    elapsed = time.time() - start

    print()
    print("=" * 50)
    print("🎉 Episode generated!")
    print(f"  📹 Video:      {result['video']}")
    print(f"  🎵 Audio:      {result['audio']}")
    print(f"  💬 Subtitles:  {result['subtitles']}")
    print(f"  📝 Script:     {result['script']}")
    print(f"  🖼️  Background: {result['background']}")
    print(f"  ⏱️  Duration:   {result['duration_seconds']:.1f}s")
    print(f"  🔢 Segments:   {result['segment_count']}")
    print(f"  ⏰ Generated in {elapsed:.1f}s")
    print("=" * 50)


def cmd_voices(args):
    """Handle the 'voices' subcommand."""
    print("\n🎙️  Available Voices")
    print("=" * 60)
    for name, voice in VOICES.items():
        print(f"  {name:<12} {voice.voice_id}  — {voice.description}")
    print()
    print("Use custom voice IDs directly: --voices myVoiceId123")
    print()


def cmd_formats(args):
    """Handle the 'formats' subcommand."""
    print("\n📋 Available Formats")
    print("=" * 60)
    descriptions = {
        Format.DEBATE: "Two hosts debate opposing sides of the topic",
        Format.MONOLOGUE: "Single host deep-dive on the topic",
        Format.NEWS_RECAP: "Anchor + correspondent news-style coverage",
        Format.INTERVIEW: "Interviewer + guest conversation",
        Format.STORYTELLING: "Narrator + color commentary storytelling",
    }
    for fmt in Format:
        print(f"  {fmt.value:<16} {descriptions.get(fmt, '')}")
    print()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="podclaw",
        description="🎙️ PodClaw — One-prompt podcast production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  podclaw generate "Is AI consciousness possible?"
  podclaw generate --format debate --voices roger,george "AI Ethics"
  podclaw generate --format monologue --duration 3m "The History of Bitcoin"
  podclaw generate --script my_script.txt --voices callum "Custom Episode"
  podclaw voices
  podclaw formats
        """,
    )
    parser.add_argument("-V", "--version", action="version", version=f"podclaw {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    # ── generate ───────────────────────────────────────────────────────────
    gen_parser = subparsers.add_parser("generate", help="Generate a podcast episode")
    gen_parser.add_argument("topic", help="Topic or prompt for the episode")
    gen_parser.add_argument(
        "--format", "-f",
        default="debate",
        help="Podcast format (default: debate)",
    )
    gen_parser.add_argument(
        "--voices", "-v",
        default=None,
        help="Comma-separated voice names or IDs (default: roger,george)",
    )
    gen_parser.add_argument(
        "--duration", "-d",
        default="2m",
        help="Target duration (e.g., 90s, 2m, 1m30s) (default: 2m)",
    )
    gen_parser.add_argument(
        "--output", "-o",
        default=".",
        help="Output directory (default: current directory)",
    )
    gen_parser.add_argument(
        "--filename",
        default=None,
        help="Output filename (default: auto-generated from topic)",
    )
    gen_parser.add_argument(
        "--script", "-s",
        default=None,
        help="Path to a pre-written script file (skips generation)",
    )
    gen_parser.add_argument(
        "--no-waveform",
        action="store_true",
        help="Disable audio waveform visualization",
    )
    gen_parser.add_argument(
        "--no-subtitles",
        action="store_true",
        help="Disable burnt-in subtitles",
    )
    gen_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full error tracebacks",
    )
    gen_parser.set_defaults(func=cmd_generate)

    # ── voices ─────────────────────────────────────────────────────────────
    voices_parser = subparsers.add_parser("voices", help="List available voices")
    voices_parser.set_defaults(func=cmd_voices)

    # ── formats ────────────────────────────────────────────────────────────
    formats_parser = subparsers.add_parser("formats", help="List available formats")
    formats_parser.set_defaults(func=cmd_formats)

    # Parse
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
