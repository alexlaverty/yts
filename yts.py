#!/usr/bin/env python3
"""Summarize YouTube videos by extracting subtitles and passing them to Claude."""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yt_dlp

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def get_video_info(url: str) -> dict:
    """Fetch video metadata using yt-dlp."""
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        try:
            return ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as e:
            print(f"Error fetching video info: {e}", file=sys.stderr)
            sys.exit(1)


def extract_subtitles(url: str) -> str:
    """Download subtitles and return as cleaned plain text."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_template = str(Path(tmpdir) / "subs.%(ext)s")
        opts = {
            "quiet": True,
            "no_warnings": True,
            "writeautomaticsub": True,
            "writesubtitles": True,
            "subtitleslangs": ["en"],
            "subtitlesformat": "vtt",
            "skip_download": True,
            "outtmpl": out_template,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                ydl.download([url])
            except yt_dlp.utils.DownloadError as e:
                print(f"Error downloading subtitles: {e}", file=sys.stderr)
                sys.exit(1)

        vtt_files = list(Path(tmpdir).glob("*.vtt"))
        if not vtt_files:
            print("No English subtitles found for this video.", file=sys.stderr)
            sys.exit(1)

        raw = vtt_files[0].read_text(encoding="utf-8")
        return clean_vtt(raw)


def clean_vtt(vtt_text: str) -> str:
    """Strip VTT timestamps/headers and deduplicate lines."""
    lines = vtt_text.splitlines()
    seen = set()
    cleaned = []
    for line in lines:
        line = line.strip()
        # Skip VTT header, timestamps, blank lines, and position tags
        if (
            not line
            or line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or "-->" in line
            or line.startswith("NOTE")
            or line[0:1].isdigit() and line.strip().isdigit()
        ):
            continue
        # Strip HTML-like tags (e.g. <c>, </c>, <00:01:02.345>)
        line = re.sub(r"<[^>]+>", "", line)
        line = line.strip()
        if line and line not in seen:
            seen.add(line)
            cleaned.append(line)
    return " ".join(cleaned)


def summarize_with_claude(title: str, subtitles: str, model: str) -> str:
    """Send subtitles to Claude CLI and get a summary."""
    prompt = f"""You are summarizing a YouTube video.

Video title: "{title}"

Below are the video's subtitles/transcript. Based on these subtitles:

1. First, write a short paragraph that directly answers or addresses the video's title. Many YouTube titles are clickbait — cut through it and give the real answer upfront.

2. Then, list the key points and takeaways from the video as bullet points.

Be concise and factual. Only include information actually present in the subtitles.

--- SUBTITLES ---
{subtitles}
--- END SUBTITLES ---"""

    result = subprocess.run(
        ["claude", "-p", prompt, "--model", model],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Error calling Claude: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Summarize a YouTube video using subtitles and Claude."
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "-m", "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model to use (default: {DEFAULT_MODEL})",
    )
    args = parser.parse_args()

    print(f"Fetching video info...", file=sys.stderr)
    info = get_video_info(args.url)
    title = info.get("title", "Unknown Title")
    print(f"Title: {title}", file=sys.stderr)

    print("Extracting subtitles...", file=sys.stderr)
    subtitles = extract_subtitles(args.url)

    if len(subtitles) < 50:
        print("Subtitles too short or empty — video may not have usable captions.", file=sys.stderr)
        sys.exit(1)

    # Truncate very long transcripts to avoid token limits
    max_chars = 100_000
    if len(subtitles) > max_chars:
        subtitles = subtitles[:max_chars]
        print(f"Transcript truncated to {max_chars} characters.", file=sys.stderr)

    print(f"Summarizing with Claude ({args.model})...", file=sys.stderr)
    summary = summarize_with_claude(title, subtitles, args.model)
    print()
    print(summary)


if __name__ == "__main__":
    main()
