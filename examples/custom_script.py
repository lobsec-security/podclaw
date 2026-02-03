#!/usr/bin/env python3
"""
PodClaw — Custom script example.

Use your own script instead of auto-generation.
"""

from podclaw import PodcastGenerator, PodclawConfig

SCRIPT = """
[HOST_A] Welcome back to the show! Today we have a wild one for you.
[HOST_B] Oh yeah. We're talking about whether pineapple belongs on pizza.
[HOST_A] And I already know where you stand on this.
[HOST_B] Pineapple on pizza is a CRIME against food, and I will die on this hill.
[HOST_A] See, that's where you're wrong. The sweet and savory combination is ELITE.
[HOST_B] Elite? You're eating fruit on cheese bread. That's chaos.
[HOST_A] It's called Hawaiian pizza, and it was invented in CANADA. 
[HOST_B] That doesn't make it better! Canada also gave us Nickelback!
[HOST_A] Low blow. But the numbers don't lie — it's one of the most popular toppings worldwide.
[HOST_B] Popularity doesn't equal quality. 
[HOST_A] Agree to disagree. Thanks for listening everyone!
[HOST_B] Peace. And put the pineapple DOWN.
"""


def main():
    config = PodclawConfig(
        topic="The Great Pineapple Pizza Debate",
        voices=["roger", "callum"],
        output_dir="./output",
    )

    gen = PodcastGenerator(config)
    result = gen.generate(
        script=SCRIPT,
        on_progress=lambda stage, msg: print(f"  [{stage}] {msg}")
    )

    print(f"\n✅ Done! Video: {result['video']}")


if __name__ == "__main__":
    main()
