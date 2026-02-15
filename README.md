# yts

A CLI tool that summarizes YouTube videos by extracting subtitles with `yt-dlp` and sending them to Claude for summarization.

## Prerequisites

- Python 3.6+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — `pip install yt-dlp`
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) — for generating summaries

## Usage

```bash
python yts.py <youtube-url>
```

Specify a different Claude model with `-m`:

```bash
python yts.py <youtube-url> -m claude-sonnet-4-5-20250929
```

The default model is `claude-haiku-4-5-20251001`.

## How it works

1. Fetches video metadata (title) via the `yt-dlp` Python API
2. Downloads English subtitles (auto-generated or manual) in VTT format
3. Cleans the VTT output — strips headers, timestamps, HTML tags, and deduplicates lines
4. Sends the title and cleaned transcript to Claude, which returns:
   - A short paragraph that cuts through the title (often clickbait) and gives the real answer
   - Key points and takeaways as bullet points
5. Prints the summary to stdout (status messages go to stderr)

Transcripts longer than 100,000 characters are automatically truncated.
