"""
SRT subtitle generation from timed script segments.
"""

from pathlib import Path


def _format_srt_time(ms: int) -> str:
    """Format milliseconds as SRT timestamp: HH:MM:SS,mmm"""
    hours = ms // 3_600_000
    minutes = (ms % 3_600_000) // 60_000
    seconds = (ms % 60_000) // 1_000
    millis = ms % 1_000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _split_long_text(text: str, max_chars: int = 80) -> list[str]:
    """Split long text into subtitle-friendly chunks."""
    if len(text) <= max_chars:
        return [text]

    words = text.split()
    lines = []
    current = []
    current_len = 0

    for word in words:
        if current_len + len(word) + 1 > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += len(word) + 1

    if current:
        lines.append(" ".join(current))

    return lines


def generate_srt(
    segments: list[dict],
    timings: list[dict],
    output_path: Path,
    max_chars_per_line: int = 80,
    show_speaker_names: bool = False,
) -> Path:
    """
    Generate an SRT subtitle file from timed segments.

    Args:
        segments: List of {"speaker", "text", ...} dicts.
        timings: List of {"start_ms", "end_ms"} dicts (parallel to segments).
        output_path: Where to save the .srt file.
        max_chars_per_line: Maximum characters per subtitle line.
        show_speaker_names: Whether to prefix lines with speaker names.

    Returns:
        Path to the generated SRT file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    srt_entries = []
    entry_index = 1

    for seg, timing in zip(segments, timings):
        text = seg["text"]
        if show_speaker_names:
            text = f"[{seg['speaker']}] {text}"

        # Split long segments into subtitle chunks
        chunks = _split_long_text(text, max_chars_per_line)

        # Distribute timing across chunks
        total_ms = timing["end_ms"] - timing["start_ms"]
        ms_per_chunk = total_ms // max(len(chunks), 1)

        for i, chunk in enumerate(chunks):
            start = timing["start_ms"] + (i * ms_per_chunk)
            end = timing["start_ms"] + ((i + 1) * ms_per_chunk)
            if i == len(chunks) - 1:
                end = timing["end_ms"]

            srt_entries.append(
                f"{entry_index}\n"
                f"{_format_srt_time(start)} --> {_format_srt_time(end)}\n"
                f"{chunk}\n"
            )
            entry_index += 1

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))

    return output_path


def generate_srt_from_text(
    full_text: str,
    total_duration_ms: int,
    output_path: Path,
) -> Path:
    """
    Generate a simple SRT file by evenly distributing text across the duration.
    Useful when exact timings aren't available.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sentences = []
    for line in full_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Strip speaker tags for subtitle display
        if line.startswith("[") and "]" in line:
            line = line[line.index("]") + 1:].strip()
        if line:
            sentences.append(line)

    if not sentences:
        output_path.write_text("")
        return output_path

    ms_per_sentence = total_duration_ms // len(sentences)
    entries = []

    for i, sentence in enumerate(sentences):
        start = i * ms_per_sentence
        end = (i + 1) * ms_per_sentence - 100  # Small gap
        chunks = _split_long_text(sentence)

        for j, chunk in enumerate(chunks):
            chunk_start = start + j * (ms_per_sentence // max(len(chunks), 1))
            chunk_end = start + (j + 1) * (ms_per_sentence // max(len(chunks), 1))
            if j == len(chunks) - 1:
                chunk_end = end

            entries.append(
                f"{len(entries) + 1}\n"
                f"{_format_srt_time(chunk_start)} --> {_format_srt_time(chunk_end)}\n"
                f"{chunk}\n"
            )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(entries))

    return output_path
