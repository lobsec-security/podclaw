"""
Script generation templates for different podcast formats.

Each template produces a structured script with speaker tags
that the TTS engine uses for voice assignment.
"""

from podclaw.config import Format, PodclawConfig


# ─── Format Templates ─────────────────────────────────────────────────────────

TEMPLATES = {
    Format.DEBATE: """Write a lively, entertaining podcast debate script between two hosts.

Topic: {topic}
Target duration: {duration} (approximately {word_count} words)

FORMAT RULES:
- Two speakers: HOST_A and HOST_B
- HOST_A takes the "for" position, HOST_B takes the "against" position
- Each line must start with the speaker tag: [HOST_A] or [HOST_B]
- Keep it conversational, witty, and engaging - not dry or academic
- Include back-and-forth rebuttals, interruptions feel natural
- Open with a brief intro from HOST_A, close with both summarizing
- Use humor, analogies, and real-world examples
- Avoid filler phrases like "That's a great point"

Example line format:
[HOST_A] Welcome to the show! Today we're diving into {topic}...
[HOST_B] And I'm here to tell you why that's completely wrong.

Write the full script now:""",

    Format.MONOLOGUE: """Write an engaging solo podcast monologue script.

Topic: {topic}
Target duration: {duration} (approximately {word_count} words)

FORMAT RULES:
- Single speaker: HOST
- Each line starts with [HOST]
- Conversational tone - like talking to a friend
- Use rhetorical questions to keep listeners engaged
- Include personal anecdotes or hypothetical stories
- Break into clear sections with natural transitions
- Open strong with a hook, close with a takeaway

Example line format:
[HOST] You know what nobody talks about? {topic}. And today, we're going there.

Write the full script now:""",

    Format.NEWS_RECAP: """Write a punchy, fast-paced news recap podcast script.

Topic: {topic}
Target duration: {duration} (approximately {word_count} words)

FORMAT RULES:
- Two speakers: ANCHOR and CORRESPONDENT
- Each line starts with [ANCHOR] or [CORRESPONDENT]
- ANCHOR introduces stories and asks questions
- CORRESPONDENT provides details and analysis
- Cover 3-5 angles or stories related to the topic
- Keep segments short and punchy
- Use transitions like "Moving on..." or "But here's the thing..."
- Open with headlines, close with a quick recap

Example line format:
[ANCHOR] Breaking news from the world of {topic}. Let's get into it.
[CORRESPONDENT] The big story today...

Write the full script now:""",

    Format.INTERVIEW: """Write a compelling podcast interview script.

Topic: {topic}
Target duration: {duration} (approximately {word_count} words)

FORMAT RULES:
- Two speakers: INTERVIEWER and GUEST
- Each line starts with [INTERVIEWER] or [GUEST]
- INTERVIEWER asks smart, probing questions
- GUEST gives detailed, interesting answers with stories
- Build from simple to complex questions
- Include follow-up questions that show active listening
- Open with a warm introduction of the guest
- Close with a rapid-fire segment or key takeaway

Example line format:
[INTERVIEWER] Welcome to the show! I've been dying to ask you about {topic}.
[GUEST] Thanks for having me. Where do I even start...

Write the full script now:""",

    Format.STORYTELLING: """Write a captivating storytelling podcast script.

Topic: {topic}
Target duration: {duration} (approximately {word_count} words)

FORMAT RULES:
- Two speakers: NARRATOR and COLOR (color commentary / reactions)
- Each line starts with [NARRATOR] or [COLOR]
- NARRATOR drives the story forward
- COLOR adds reactions, questions, and humor
- Build tension with a clear narrative arc
- Use vivid descriptions and dialogue
- Include a twist or surprising element
- Open with an atmospheric hook, close with a reflection

Example line format:
[NARRATOR] Picture this. It's 3 AM, and something just went very, very wrong.
[COLOR] Oh no. I already don't like where this is going.

Write the full script now:""",
}


# ─── Speaker Role Mapping ──────────────────────────────────────────────────────

SPEAKER_ROLES = {
    Format.DEBATE: ["HOST_A", "HOST_B"],
    Format.MONOLOGUE: ["HOST"],
    Format.NEWS_RECAP: ["ANCHOR", "CORRESPONDENT"],
    Format.INTERVIEW: ["INTERVIEWER", "GUEST"],
    Format.STORYTELLING: ["NARRATOR", "COLOR"],
}


def estimate_word_count(duration_seconds: int) -> int:
    """Estimate word count from target duration (~150 words/minute for natural speech)."""
    return int(duration_seconds * 150 / 60)


def format_duration(seconds: int) -> str:
    """Format seconds into a human-readable duration string."""
    minutes = seconds // 60
    remaining = seconds % 60
    if minutes == 0:
        return f"{remaining} seconds"
    if remaining == 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    return f"{minutes}m {remaining}s"


def generate_prompt(config: PodclawConfig) -> str:
    """Generate the LLM prompt for script generation."""
    template = TEMPLATES[config.format]
    word_count = estimate_word_count(config.duration_seconds)
    duration = format_duration(config.duration_seconds)

    return template.format(
        topic=config.topic,
        duration=duration,
        word_count=word_count,
    )


def parse_script(raw_script: str) -> list[dict]:
    """
    Parse a tagged script into structured segments.

    Returns a list of dicts: [{"speaker": "HOST_A", "text": "..."}, ...]
    """
    segments = []
    current_speaker = None
    current_text = []

    for line in raw_script.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # Check for speaker tag: [SPEAKER_NAME]
        if line.startswith("[") and "]" in line:
            # Flush previous segment
            if current_speaker and current_text:
                segments.append({
                    "speaker": current_speaker,
                    "text": " ".join(current_text).strip(),
                })
                current_text = []

            bracket_end = line.index("]")
            current_speaker = line[1:bracket_end].strip()
            remaining = line[bracket_end + 1:].strip()
            if remaining:
                current_text.append(remaining)
        elif current_speaker:
            current_text.append(line)

    # Flush last segment
    if current_speaker and current_text:
        segments.append({
            "speaker": current_speaker,
            "text": " ".join(current_text).strip(),
        })

    return segments


def assign_voices(segments: list[dict], config: PodclawConfig) -> list[dict]:
    """
    Assign voice configurations to script segments based on speaker roles.

    Maps speakers to voices in order (first unique speaker → first voice, etc.).
    """
    voices = config.get_all_voices()
    speaker_to_voice = {}

    for seg in segments:
        speaker = seg["speaker"]
        if speaker not in speaker_to_voice:
            voice_index = len(speaker_to_voice) % len(voices)
            speaker_to_voice[speaker] = voices[voice_index]

    result = []
    for seg in segments:
        result.append({
            **seg,
            "voice": speaker_to_voice[seg["speaker"]],
        })

    return result


def generate_demo_script(config: PodclawConfig) -> str:
    """
    Generate a demo script without needing an LLM.
    Uses the topic to create a basic but functional script.
    """
    voices = config.get_all_voices()
    roles = SPEAKER_ROLES.get(config.format, ["HOST_A", "HOST_B"])

    if config.format == Format.MONOLOGUE:
        return f"""[HOST] Welcome to the show! Today we're diving deep into {config.topic}.
[HOST] This is one of those topics that everyone has an opinion on, but very few people actually understand.
[HOST] So let me break it down for you.
[HOST] First off, let's talk about why {config.topic} matters right now.
[HOST] The world is changing fast, and this is at the center of it.
[HOST] Here's what most people get wrong about it.
[HOST] They think it's simple. It's not. It's layers upon layers of complexity.
[HOST] But here's the good news - once you understand the core principle, everything else clicks.
[HOST] And that core principle? It all comes down to one thing.
[HOST] Incentives. Follow the incentives, and you'll understand {config.topic}.
[HOST] That's all for today. Thanks for listening, and I'll catch you in the next one."""

    if config.format == Format.NEWS_RECAP:
        return f"""[ANCHOR] Good evening! Top stories tonight - major developments in {config.topic}.
[CORRESPONDENT] That's right. We've been tracking this all week, and things are heating up.
[ANCHOR] Give us the rundown.
[CORRESPONDENT] Three big developments. First, the landscape has shifted dramatically.
[ANCHOR] How so?
[CORRESPONDENT] New players are entering the space, and the old guard isn't happy about it.
[ANCHOR] And the second development?
[CORRESPONDENT] The numbers are in, and they're surprising everyone. Way higher than expected.
[ANCHOR] That's significant. And the third?
[CORRESPONDENT] Perhaps most importantly - the regulatory picture is changing.
[ANCHOR] What does this mean for the average person?
[CORRESPONDENT] It means {config.topic} is about to affect everyone, whether they're paying attention or not.
[ANCHOR] That's all the time we have. Stay informed, stay sharp."""

    # Default: debate/interview/storytelling (two speakers)
    a, b = roles[0], roles[1] if len(roles) > 1 else roles[0]
    return f"""[{a}] Welcome to the show! Today we're tackling {config.topic}.
[{b}] Oh, this is going to be good. I have STRONG opinions on this one.
[{a}] I know you do. So let's get right into it. Where do you stand?
[{b}] Here's the thing - most people are looking at {config.topic} completely wrong.
[{a}] Wrong how? Walk me through it.
[{b}] They're focused on the surface level. The flashy stuff. But the real story is underneath.
[{a}] Okay, I'll push back on that. The surface level matters because that's what people experience.
[{b}] Sure, but if you only look at what's visible, you miss the entire mechanism driving it.
[{a}] Fair point. So what's the mechanism?
[{b}] It comes down to three things. Money, power, and timing.
[{a}] The holy trinity.
[{b}] Exactly. And right now, the timing couldn't be more critical.
[{a}] This has been a fantastic discussion. Thanks for tuning in everyone!
[{b}] Peace!"""
