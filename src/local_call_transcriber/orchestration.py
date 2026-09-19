"""Coordinación del flujo de transcripción para un archivo."""

from dataclasses import dataclass
from pathlib import Path

from local_call_transcriber.engines.base import TranscriptionEngine
from local_call_transcriber.outputs import write_json, write_txt


class InputValidationError(ValueError):
    """La entrada no es apta para la transcripción baseline."""


@dataclass(frozen=True)
class OutputPaths:
    txt: Path
    json: Path


def validate_mp4(media_path: Path) -> None:
    if not media_path.is_file():
        raise InputValidationError(f"No existe el archivo de entrada: {media_path}")
    if media_path.suffix.lower() != ".mp4":
        raise InputValidationError("El baseline CPU acepta únicamente archivos MP4 (.mp4).")


def transcribe_file(
    engine: TranscriptionEngine,
    media_path: Path,
    output_dir: Path,
    language: str | None,
    vad: bool,
) -> OutputPaths:
    validate_mp4(media_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = engine.transcribe(media_path=media_path, language=language, vad=vad)
    txt_path = output_dir / f"{media_path.stem}.txt"
    json_path = output_dir / f"{media_path.stem}.json"
    write_txt(result, txt_path)
    write_json(result, json_path)
    return OutputPaths(txt=txt_path, json=json_path)
