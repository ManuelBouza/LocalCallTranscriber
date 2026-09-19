"""Serialización de resultados iniciales de transcripción."""

import json
from pathlib import Path

from local_call_transcriber.domain import TranscriptResult


def write_txt(result: TranscriptResult, destination: Path) -> None:
    destination.write_text("\n".join(segment.text for segment in result.segments) + "\n", encoding="utf-8")


def write_json(result: TranscriptResult, destination: Path) -> None:
    destination.write_text(
        json.dumps(result.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def format_timestamp(seconds: float, separator: str) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02}{separator}{milliseconds:03}"


def write_srt(result: TranscriptResult, destination: Path) -> None:
    blocks = []
    for index, segment in enumerate(sorted(result.segments, key=lambda item: item.start), start=1):
        blocks.append(
            f"{index}\n{format_timestamp(segment.start, ',')} --> {format_timestamp(segment.end, ',')}\n"
            f"{segment.text}"
        )
    destination.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def write_vtt(result: TranscriptResult, destination: Path) -> None:
    blocks = ["WEBVTT"]
    for segment in sorted(result.segments, key=lambda item: item.start):
        blocks.append(
            f"{format_timestamp(segment.start, '.')} --> {format_timestamp(segment.end, '.')}\n"
            f"{segment.text}"
        )
    destination.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
