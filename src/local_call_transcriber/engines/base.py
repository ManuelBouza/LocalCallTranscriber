"""Contrato común para motores de transcripción."""

from pathlib import Path
from typing import Protocol

from local_call_transcriber.domain import TranscriptResult


class TranscriptionEngine(Protocol):
    def transcribe(self, media_path: Path, language: str | None, vad: bool) -> TranscriptResult:
        """Transcribe un archivo local y devuelve un resultado independiente del motor."""
