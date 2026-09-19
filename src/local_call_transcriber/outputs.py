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
