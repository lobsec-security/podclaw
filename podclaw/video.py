"""
Video assembly: background generation + ffmpeg composition.

Creates the final MP4 from background image, audio, waveform, and subtitles.
"""

import subprocess
from pathlib import Path
from typing import Optional


def create_background(
    output_path: Path,
    width: int = 1920,
    height: int = 1080,
    bg_color: tuple[int, int, int] = (10, 22, 40),
    accent_color: tuple[int, int, int] = (218, 165, 32),
    text_color: tuple[int, int, int] = (255, 253, 240),
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
) -> Path:
    """
    Create a podcast background image using Pillow.

    Args:
        output_path: Where to save the PNG.
        width: Video width.
        height: Video height.
        bg_color: Background RGB color.
        accent_color: Accent/decoration RGB color.
        text_color: Text RGB color.
        title: Main title text.
        subtitle: Subtitle text.

    Returns:
        Path to the generated image.
    """
    from PIL import Image, ImageDraw, ImageFont
    import math

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(height):
        factor = 1.0 - (y / height) * 0.2
        color = tuple(int(c * factor) for c in bg_color)
        draw.line([(0, y), (width, y)], fill=color)

    # Decorative border
    margin = 45
    draw.rectangle(
        [margin, margin, width - margin, height - margin],
        outline=accent_color,
        width=3,
    )
    draw.rectangle(
        [margin + 8, margin + 8, width - margin - 8, height - margin - 8],
        outline=accent_color,
        width=1,
    )

    # Corner decorations
    corner_size = 20
    for cx, cy in [
        (margin + 20, margin + 20),
        (width - margin - 20, margin + 20),
        (margin + 20, height - margin - 20),
        (width - margin - 20, height - margin - 20),
    ]:
        draw.rectangle(
            [cx - corner_size // 2, cy - corner_size // 2,
             cx + corner_size // 2, cy + corner_size // 2],
            outline=accent_color, width=2,
        )

    # Side decorative stars
    def draw_star(cx, cy, size=12):
        points = []
        for i in range(8):
            angle = math.radians(i * 45 - 90)
            r = size if i % 2 == 0 else size * 0.4
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        draw.polygon(points, fill=accent_color)

    star_positions = [
        (200, 100), (width - 200, 100),
        (200, height - 100), (width - 200, height - 100),
        (100, height // 2), (width - 100, height // 2),
    ]
    for sx, sy in star_positions:
        draw_star(sx, sy)

    # Load fonts with cross-platform fallback
    def load_font(size: int, bold: bool = False):
        font_candidates = [
            # macOS
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold
            else "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
            else "/System/Library/Fonts/Supplemental/Arial.ttf",
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        for path in font_candidates:
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()

    # Title
    if title:
        font_title = load_font(64, bold=True)
        bbox = draw.textbbox((0, 0), title, font=font_title)
        tw = bbox[2] - bbox[0]
        tx = (width - tw) // 2
        ty = height // 2 - 80
        # Shadow
        draw.text((tx + 3, ty + 3), title, font=font_title, fill=(0, 0, 0))
        draw.text((tx, ty), title, font=font_title, fill=text_color)

    # Subtitle
    if subtitle:
        font_sub = load_font(36)
        bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
        sw = bbox[2] - bbox[0]
        sx = (width - sw) // 2
        sy = height // 2 + 20
        draw.text((sx, sy), subtitle, font=font_sub, fill=accent_color)

    # "Generated with PodClaw" watermark (subtle)
    font_wm = load_font(22)
    wm_text = "Generated with PodClaw"
    bbox = draw.textbbox((0, 0), wm_text, font=font_wm)
    ww = bbox[2] - bbox[0]
    draw.text(
        ((width - ww) // 2, height - 80),
        wm_text,
        font=font_wm,
        fill=tuple(max(c - 60, 0) for c in bg_color),  # Very subtle
    )

    img.save(output_path, quality=95)
    return output_path


def assemble_video(
    background_path: Path,
    audio_path: Path,
    output_path: Path,
    srt_path: Optional[Path] = None,
    show_waveform: bool = True,
    subtitle_font_size: int = 28,
    subtitle_margin_v: int = 60,
    subtitle_outline: int = 3,
    audio_bitrate: str = "192k",
    duration: Optional[float] = None,
) -> Path:
    """
    Assemble the final video using ffmpeg.

    Combines:
    - Static background image
    - Audio track
    - Optional waveform visualization
    - Optional burnt-in subtitles

    Args:
        background_path: Path to background image.
        audio_path: Path to audio file.
        output_path: Where to save the MP4.
        srt_path: Optional path to SRT subtitle file.
        show_waveform: Whether to add audio waveform visualization.
        subtitle_font_size: Font size for subtitles.
        subtitle_margin_v: Vertical margin for subtitles.
        subtitle_outline: Outline width for subtitles.
        audio_bitrate: Audio encoding bitrate.
        duration: Optional duration limit in seconds.

    Returns:
        Path to the generated MP4.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build filter chain
    filters = []

    has_subtitles = srt_path and srt_path.exists()

    if show_waveform:
        # Waveform visualization: show audio as oscilloscope at bottom
        out_label = "[vtmp]" if has_subtitles else "[vout]"
        filters.append(
            f"[1:a]showwaves=s=1920x120:mode=cline:rate=30:"
            f"colors=0xDAA520@0.7:scale=sqrt[wave];"
            f"[0:v][wave]overlay=0:H-180{out_label}"
        )
        video_label = out_label
    else:
        video_label = "[0:v]"

    if has_subtitles:
        srt_escaped = str(srt_path).replace(":", r"\:").replace("'", r"\'")
        subtitle_style = (
            f"FontSize={subtitle_font_size},"
            f"FontName=Arial,"
            f"PrimaryColour=&HFFFFFF&,"
            f"OutlineColour=&H000000&,"
            f"BackColour=&H80000000&,"
            f"Outline={subtitle_outline},"
            f"Shadow=2,"
            f"MarginV={subtitle_margin_v},"
            f"Bold=1"
        )
        filters.append(
            f"{video_label}subtitles='{srt_escaped}':"
            f"force_style='{subtitle_style}'[vout]"
        )
        video_label = "[vout]"

    # Build ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(background_path),
        "-i", str(audio_path),
    ]

    if filters:
        filter_complex = ";".join(filters)
        cmd.extend(["-filter_complex", filter_complex])
        cmd.extend(["-map", video_label, "-map", "1:a"])
    else:
        cmd.extend(["-map", "0:v", "-map", "1:a"])

    cmd.extend([
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        "-pix_fmt", "yuv420p",
        "-shortest",
    ])

    if duration:
        cmd.extend(["-t", str(duration)])

    cmd.append(str(output_path))

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed with code {result.returncode}:\n{result.stderr}"
        )

    return output_path


def get_audio_duration(audio_path: str) -> float:
    """Get audio file duration in seconds."""
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
    return float(result.stdout.strip())
