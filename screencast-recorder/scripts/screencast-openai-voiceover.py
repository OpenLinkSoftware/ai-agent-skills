#!/usr/bin/env python3
"""Generate an MP3 voice-over for a screencast using OpenAI text-to-speech."""

from __future__ import annotations

import argparse
from pathlib import Path

from openai import OpenAI


DEFAULT_INSTRUCTIONS = (
    "Speak as a calm, confident technical narrator. Keep the pace measured and "
    "clear. Avoid hype; make it sound like a concise product explainer for an "
    "expert audience."
)


def read_text(value: str | None, file_path: str | None) -> str:
    if value and file_path:
        raise SystemExit("Use either --text or --text-file, not both.")
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    if value:
        return value.strip()
    raise SystemExit("Provide narration with --text or --text-file.")


def read_optional_text(value: str | None, file_path: str | None, default: str) -> str:
    if value and file_path:
        raise SystemExit("Use either --instructions or --instructions-file, not both.")
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    if value:
        return value.strip()
    return default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an MP3 narration track for a screencast."
    )
    parser.add_argument("--text", help="Narration text to synthesize.")
    parser.add_argument("--text-file", help="UTF-8 file containing narration text.")
    parser.add_argument("--output", required=True, help="Output MP3 path.")
    parser.add_argument("--voice", default="coral", help="OpenAI TTS voice.")
    parser.add_argument("--model", default="gpt-4o-mini-tts", help="OpenAI TTS model.")
    parser.add_argument("--instructions", help="Voice delivery instructions.")
    parser.add_argument("--instructions-file", help="UTF-8 file with voice instructions.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    narration = read_text(args.text, args.text_file)
    instructions = read_optional_text(
        args.instructions,
        args.instructions_file,
        DEFAULT_INSTRUCTIONS,
    )
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    client = OpenAI()
    with client.audio.speech.with_streaming_response.create(
        model=args.model,
        voice=args.voice,
        input=narration,
        instructions=instructions,
    ) as response:
        response.stream_to_file(output)

    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
