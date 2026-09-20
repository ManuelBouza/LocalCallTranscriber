"""Capa de aplicación compartida por las interfaces de usuario.

El CLI y la GUI construyen :class:`TranscriptionRequest` y delegan aquí; esta capa
no conoce argumentos de terminal ni bibliotecas de interfaz gráfica.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from local_call_transcriber.engines.base import TranscriptionEngine
from local_call_transcriber.engines.faster_whisper import FasterWhisperEngine
from local_call_transcriber.orchestration import (
    CancellationCheck,
    FolderItemFinished,
    FolderItemResult,
    FolderItemStarted,
    OutputPaths,
    transcribe_file,
    transcribe_folder,
)


@dataclass(frozen=True)
class TranscriptionRequest:
    """Configuración completa de una operación de archivo o carpeta local."""

    input_path: Path
    output_dir: Path
    model: str = "large-v3-turbo"
    language: str | None = None
    device: str = "auto"
    compute_type: str = "auto"
    vad: bool = True
    word_timestamps: bool = False
    overwrite: bool = False
    model_cache: Path | None = None


@dataclass(frozen=True)
class FileTranscriptionRun:
    outputs: OutputPaths


@dataclass(frozen=True)
class FolderTranscriptionRun:
    results: tuple[FolderItemResult, ...]
    cancelled: bool = False
    total: int = 0


TranscriptionRun = FileTranscriptionRun | FolderTranscriptionRun
EngineFactory = Callable[[TranscriptionRequest], TranscriptionEngine]


def default_model_cache() -> Path:
    """Devuelve el directorio local de modelos sin crear ni modificar nada."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "LocalCallTranscriber" / "models"
    return Path.home() / ".cache" / "LocalCallTranscriber" / "models"


def create_engine(request: TranscriptionRequest) -> TranscriptionEngine:
    """Construye el adaptador de producción desde una solicitud independiente de UI."""
    return FasterWhisperEngine(
        model_name=request.model,
        model_cache=request.model_cache or default_model_cache(),
        device=request.device,
        compute_type=request.compute_type,
    )


class TranscriptionApplication:
    """Ejecuta una solicitud usando el único pipeline de transcripción del proyecto."""

    def __init__(self, engine_factory: EngineFactory = create_engine) -> None:
        self._engine_factory = engine_factory

    def run(
        self,
        request: TranscriptionRequest,
        *,
        on_item_started: FolderItemStarted | None = None,
        on_item_finished: FolderItemFinished | None = None,
        should_cancel: CancellationCheck | None = None,
    ) -> TranscriptionRun:
        engine = self._engine_factory(request)

        if request.input_path.is_dir():
            total = sum(1 for _ in request.input_path.glob("*.mp4"))
            results = transcribe_folder(
                engine,
                request.input_path,
                request.output_dir,
                request.language,
                request.vad,
                request.word_timestamps,
                request.overwrite,
                on_item_started=on_item_started,
                on_item_finished=on_item_finished,
                should_cancel=should_cancel,
            )
            cancelled = (
                should_cancel is not None
                and should_cancel()
                and len(results) < total
            )
            return FolderTranscriptionRun(
                results=results,
                cancelled=cancelled,
                total=total,
            )

        if on_item_started is not None:
            on_item_started(request.input_path, 1, 1)

        outputs = transcribe_file(
            engine,
            request.input_path,
            request.output_dir,
            request.language,
            request.vad,
            request.word_timestamps,
            request.overwrite,
        )

        if on_item_finished is not None:
            on_item_finished(
                FolderItemResult(
                    request.input_path,
                    "success",
                    "Salidas generadas.",
                ),
                1,
                1,
            )

        return FileTranscriptionRun(outputs)
