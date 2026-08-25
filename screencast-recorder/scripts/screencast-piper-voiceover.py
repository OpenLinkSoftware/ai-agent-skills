#!/usr/bin/env python3
"""Generate an MP3 voice-over for a screencast using Piper (local, offline TTS).

Optional dependency: nothing installs at skill-load time. This script installs
`piper-tts` (pip) and downloads the requested voice model (one-time, ~50-120MB
depending on quality tier) only when actually run -- and only if not already
present. Use this as a fallback when OpenAI TTS is unreachable or out of quota.

Trade-off vs. the OpenAI path: Piper has no style/instructions prompt. It is
fixed-voice, fixed-prosody synthesis -- only speed (--length-scale), variation
(--noise-scale / --noise-w-scale), and volume are tunable. There is no way to
ask for "steady, unhurried power" the way screencast-openai-voiceover.py's
--instructions can.

This script's defaults are tuned as the closest numeric PROXY for a steady,
measured, "in-control" delivery -- flatter variation (lower noise scales) and
a touch slower than Piper's stock defaults (noise_scale=0.667, noise_w_scale=
0.8, length_scale=1.0). It is an approximation, not real style control: it
cannot add emphasis, warmth, urgency, or any other directed quality. If the
narration needs a genuinely different delivery style, that requires a cloud
TTS with a style prompt (OpenAI, ElevenLabs, Azure's SSML express-as, etc.),
not a Piper flag change.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import wave
from pathlib import Path

DEFAULT_VOICE = "en_US-ryan-high"
VOICE_CACHE_DIR = Path.home() / ".cache" / "piper-voices"


def read_text(value: str | None, file_path: str | None) -> str:
    if value and file_path:
        raise SystemExit("Use either --text or --text-file, not both.")
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    if value:
        return value.strip()
    raise SystemExit("Provide narration with --text or --text-file.")


def ensure_piper_installed() -> None:
    try:
        import piper  # noqa: F401
        return
    except ImportError:
        pass
    print("piper-tts not installed -- installing now (pip install piper-tts)...", file=sys.stderr)
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "piper-tts"], check=True)


def ensure_voice_downloaded(voice: str, data_dir: Path) -> Path:
    model_path = data_dir / f"{voice}.onnx"
    config_path = data_dir / f"{voice}.onnx.json"
    if model_path.exists() and config_path.exists():
        return model_path
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"Voice model {voice} not found in {data_dir} -- downloading now...", file=sys.stderr)
    subprocess.run(
        [sys.executable, "-m", "piper.download_voices", voice, "--data-dir", str(data_dir)],
        check=True,
    )
    if not model_path.exists():
        raise SystemExit(f"Download completed but {model_path} still missing -- check voice name.")
    return model_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an MP3 narration track for a screencast using local Piper TTS."
    )
    parser.add_argument("--text", help="Narration text to synthesize.")
    parser.add_argument("--text-file", help="UTF-8 file containing narration text.")
    parser.add_argument("--output", required=True, help="Output MP3 path.")
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"Piper voice name, e.g. en_US-ryan-high, en_US-norman-medium, "
             f"en_GB-alan-medium (default: {DEFAULT_VOICE}).",
    )
    parser.add_argument(
        "--data-dir",
        default=str(VOICE_CACHE_DIR),
        help=f"Directory to cache/download voice models (default: {VOICE_CACHE_DIR}).",
    )
    parser.add_argument(
        "--length-scale",
        type=float,
        default=1.05,
        help="Speed multiplier; >1.0 is slower, <1.0 is faster "
             "(default: 1.05 -- a touch slower than Piper's stock 1.0, for a more "
             "deliberate/steady pace; not real style control, see module docstring).",
    )
    parser.add_argument(
        "--noise-scale",
        type=float,
        default=0.5,
        help="Pitch/audio variation; lower is flatter/steadier "
             "(default: 0.5, down from Piper's stock 0.667, for an evener delivery).",
    )
    parser.add_argument(
        "--noise-w-scale",
        type=float,
        default=0.6,
        help="Speaking-rate variation; lower is more even/metronomic "
             "(default: 0.6, down from Piper's stock 0.8).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    narration = read_text(args.text, args.text_file)
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required to convert Piper's WAV output to MP3.")

    ensure_piper_installed()

    from piper import PiperVoice
    from piper.config import SynthesisConfig

    data_dir = Path(args.data_dir).expanduser()
    model_path = ensure_voice_downloaded(args.voice, data_dir)

    voice = PiperVoice.load(str(model_path))
    syn_config = SynthesisConfig(
        length_scale=args.length_scale,
        noise_scale=args.noise_scale,
        noise_w_scale=args.noise_w_scale,
    )

    wav_path = output.with_suffix(".wav")
    with wave.open(str(wav_path), "wb") as wav_file:
        voice.synthesize_wav(narration, wav_file, syn_config=syn_config)

    subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-qscale:a", "2",
         str(output), "-loglevel", "error"],
        check=True,
    )
    wav_path.unlink()

    print(
        f"Wrote {output}  (voice={args.voice}, length_scale={args.length_scale}, "
        f"noise_scale={args.noise_scale}, noise_w_scale={args.noise_w_scale} -- "
        f"numeric proxy for steady delivery, not real style control; see module docstring)"
    )


if __name__ == "__main__":
    main()
