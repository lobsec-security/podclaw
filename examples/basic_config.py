#!/usr/bin/env python3
"""
PodClaw — Basic usage example.

Generates a debate-format episode with default voices.
"""

from podclaw import PodcastGenerator, PodclawConfig, Format


def main():
    config = PodclawConfig(
        topic="Is social media making us smarter or dumber?",
        format=Format.DEBATE,
        voices=["roger", "george"],
        duration_seconds=120,
        output_dir="./output",
    )

    gen = PodcastGenerator(config)
    result = gen.generate(
        on_progress=lambda stage, msg: print(f"  [{stage}] {msg}")
    )

    print(f"\n✅ Done! Video: {result['video']}")


if __name__ == "__main__":
    main()
