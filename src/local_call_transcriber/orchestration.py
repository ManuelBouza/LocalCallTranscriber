"""Coordinación del flujo de transcripción para un archivo."""

import json
from dataclasses import dataclass
from pathlib import Path

from local_call_transcriber.engines.base import TranscriptionEngine
from local_call_transcriber.domain import TranscriptResult
from local_call_transcriber.outputs import write_json, write_srt, write_txt, write_vtt


class InputValidationError(ValueError):
    """La entrada no es apta para la transcripción baseline."""


@dataclass(frozen=True)
class OutputPaths:
    txt: Path
    json: Path
    srt: Path
    vtt: Path


@dataclass(frozen=True)
class FolderItemResult:
    source: Path
    status: str
    detail: str


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
    word_timestamps: bool,
    overwrite: bool,
) -> OutputPaths:
    validate_mp4(media_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = OutputPaths(
        txt=output_dir / f"{media_path.stem}.txt",
        json=output_dir / f"{media_path.stem}.json",
        srt=output_dir / f"{media_path.stem}.srt",
        vtt=output_dir / f"{media_path.stem}.vtt",
    )
    existing = [path for path in (outputs.txt, outputs.json, outputs.srt, outputs.vtt) if path.exists()]
    if existing and not overwrite:
        raise InputValidationError(
            "Ya existen salidas para esta llamada. Usa --overwrite para sustituirlas: "
            + ", ".join(str(path) for path in existing)
        )
    result = engine.transcribe(
        media_path=media_path, language=language, vad=vad, word_timestamps=word_timestamps
    )
    ordered_result = TranscriptResult(
        model=result.model,
        language=result.language,
        segments=tuple(sorted(result.segments, key=lambda segment: segment.start)),
    )
    write_txt(ordered_result, outputs.txt)
    write_json(ordered_result, outputs.json)
    write_srt(ordered_result, outputs.srt)
    write_vtt(ordered_result, outputs.vtt)
    return outputs


def transcribe_folder(
    engine: TranscriptionEngine,
    input_dir: Path,
    output_dir: Path,
    language: str | None,
    vad: bool,
    word_timestamps: bool,
    overwrite: bool,
) -> tuple[FolderItemResult, ...]:
    if not input_dir.is_dir():
        raise InputValidationError(f"No existe el directorio de entrada: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    log_path = output_dir / "folder-run.jsonl"
    for media_path in sorted(input_dir.glob("*.mp4")):
        try:
            transcribe_file(engine, media_path, output_dir, language, vad, word_timestamps, overwrite)
            item = FolderItemResult(media_path, "success", "Salidas generadas.")
        except InputValidationError as error:
            item = FolderItemResult(media_path, "skipped", str(error))
        except RuntimeError as error:
            item = FolderItemResult(media_path, "error", str(error))
        results.append(item)
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps({"file": media_path.name, "status": item.status, "detail": item.detail}, ensure_ascii=False) + "\n")
    return tuple(results)
