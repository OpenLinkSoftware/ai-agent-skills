#!/usr/bin/env python3
"""Generate screencast narration with Grok/xAI text-to-speech (default voice: leo).

One clip per scene, then (optionally) a timing plan and a standalone voice track
that fits each scene to its narration:  scene length = max(min_scene, clip + tail).

The API key is read from the XAI_API_KEY environment variable. If it is not set,
the single `export XAI_API_KEY=...` line is read from ~/.zshrc (a non-interactive
shell does not load it). The key is never printed, logged or written to a file.

Usage:
  screencast-grok-voiceover.py --scenes-dir narration-scenes --out-dir vo \
      --plan vo-plan.json --track voiceover.mp3
  screencast-grok-voiceover.py --text-file narration.txt --output voiceover.mp3
"""
import argparse, json, math, os, pathlib, re, subprocess, sys, urllib.request, urllib.error

ENDPOINT = "https://api.x.ai/v1/tts"


def get_key():
    key = os.environ.get("XAI_API_KEY", "").strip()
    if key:
        return key
    rc = pathlib.Path.home() / ".zshrc"
    if rc.exists():
        for line in rc.read_text(errors="ignore").splitlines():
            m = re.match(r"\s*export\s+XAI_API_KEY=(.*)", line)
            if m:
                return m.group(1).strip().strip("'\"")
    sys.exit("XAI_API_KEY is not set and no 'export XAI_API_KEY=' line was found in ~/.zshrc")


def tts(text, voice, key, language="en"):
    body = json.dumps({"text": text, "voice_id": voice, "language": language, "text_normalization": True}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST",
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"TTS failed: HTTP {e.code} {e.read()[:200].decode(errors='replace')}")


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(path)]).decode())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--voice", default="leo", help="xAI voice id (default leo; rex is the documented fallback)")
    ap.add_argument("--text-file", help="single narration file -> --output")
    ap.add_argument("--output", help="MP3 path for --text-file mode")
    ap.add_argument("--scenes-dir", help="directory of NN-name.txt files, one per scene")
    ap.add_argument("--out-dir", default="vo", help="per-scene MP3 output directory")
    ap.add_argument("--plan", help="write a JSON timing plan here")
    ap.add_argument("--track", help="write a standalone voice track MP3 here (needs --plan)")
    ap.add_argument("--min-scene", type=float, default=0.0, help="minimum scene length in seconds")
    ap.add_argument("--tail", type=float, default=1.0, help="seconds added after each clip (default 1.0)")
    ap.add_argument("--lead", type=float, default=0.4, help="silence before each clip inside its scene")
    a = ap.parse_args()
    key = get_key()

    if a.text_file:
        if not a.output:
            sys.exit("--output is required with --text-file")
        data = tts(pathlib.Path(a.text_file).read_text().strip(), a.voice, key)
        pathlib.Path(a.output).write_bytes(data)
        print(f"voice={a.voice} {duration(a.output):.2f}s -> {a.output}")
        return

    if not a.scenes_dir:
        sys.exit("give --text-file or --scenes-dir")
    out = pathlib.Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    names = []
    for txt in sorted(pathlib.Path(a.scenes_dir).glob("*.txt")):
        (out / f"{txt.stem}.mp3").write_bytes(tts(txt.read_text().strip(), a.voice, key))
        names.append(txt.stem)
        print(f"voice={a.voice} {txt.stem} {duration(out / (txt.stem + '.mp3')):.2f}s")

    if a.plan:
        start, rows = 0.0, []
        for n in names:
            ad = duration(out / f"{n}.mp3")
            dur = round(math.ceil(max(a.min_scene, ad + a.tail) * 10 - 1e-9) / 10, 1)
            rows.append({"name": n, "start": round(start, 1), "duration": dur, "audio": round(ad, 3)})
            start += dur
        pathlib.Path(a.plan).write_text(json.dumps({"lead": a.lead, "scenes": rows, "total": round(start, 1)}, indent=1))
        print(f"plan -> {a.plan} (total {start:.1f}s)")
        if a.track:
            parts = []
            for r in rows:
                w = out / f"pad-{r['name']}.wav"
                ms = int(a.lead * 1000)
                subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", str(out / f"{r['name']}.mp3"), "-af",
                                       f"adelay={ms}|{ms},apad", "-t", str(r["duration"]), "-ar", "44100", "-ac", "2",
                                       "-c:a", "pcm_s16le", str(w)])
                parts.append(w.name)
            (out / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
            subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(out / "list.txt"),
                                   "-af", "apad=pad_dur=1.0", "-c:a", "libmp3lame", "-b:a", "160k", a.track])
            print(f"track -> {a.track} ({duration(a.track):.1f}s)")


if __name__ == "__main__":
    main()
