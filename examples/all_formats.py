#!/usr/bin/env python3
"""
PodClaw — Generate one episode in each format.

Demonstrates all available podcast formats.
"""

from podclaw import PodcastGenerator, PodclawConfig, Format


TOPICS = {
    Format.DEBATE: "Should AI be allowed to run companies?",
    Format.MONOLOGUE: "What I learned from losing $26 in crypto",
    Format.NEWS_RECAP: "This week in AI: agents, models, and drama",
    Format.INTERVIEW: "Inside the mind of an autonomous agent",
    Format.STORYTELLING: "The night the blockchain went dark",
}


def main():
    for fmt, topic in TOPICS.items():
        print(f"\n{'='*60}")
        print(f"Generating: {fmt.value} — {topic}")
        print(f"{'='*60}")

        config = PodclawConfig(
            topic=topic,
            format=fmt,
            voices=["roger", "george"],
            duration_seconds=90,
            output_dir=f"./output/{fmt.value}",
        )

        gen = PodcastGenerator(config)
        result = gen.generate(
            on_progress=lambda stage, msg: print(f"  [{stage}] {msg}")
        )

        print(f"  ✅ {result['video']}")

    print("\n🎉 All formats generated!")


if __name__ == "__main__":
    main()
