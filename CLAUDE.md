# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

yts is a single-file Python CLI tool that summarizes YouTube videos. It extracts subtitles via `yt-dlp`, cleans the VTT format, and sends the transcript to Claude CLI for summarization.

## Usage

```bash
python yts.py <youtube-url>
python yts.py <youtube-url> -m <model-id>
```

Default model: `claude-haiku-4-5-20251001`

## Dependencies

Python packages:
- `yt-dlp` — used as a library (`import yt_dlp`) for video metadata and subtitle extraction

External CLI tools:
- `claude` — Claude Code CLI, used to generate summaries

## Architecture

Single file `yts.py` with a linear pipeline:
1. `get_video_info()` — uses `yt_dlp` Python API to get video title
2. `extract_subtitles()` — uses `yt_dlp` Python API to download English VTT subtitles to a temp directory
3. `clean_vtt()` — strips VTT headers/timestamps/tags and deduplicates lines
4. `summarize_with_claude()` — sends title + transcript to `claude -p` as a prompt
5. `main()` — orchestrates the pipeline, truncates transcripts >100k chars

Status output goes to stderr; the summary itself goes to stdout.
