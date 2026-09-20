"""Interfaz de línea de comandos estable para personas, scripts y agentes."""

import argparse
from pathlib import Path

from local_call_transcriber.application import (
    FileTranscriptionRun,
    FolderTranscriptionRun,
    TranscriptionApplication,
    TranscriptionRequest,
)
from local_call_transcriber.hardware import COMPUTE_TYPE_CHOICES, DEVICE_CHOICES
from local_call_transcriber.orchestration import InputValidationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transcribe MP4 locales sin enviar audio ni texto fuera del equipo."
    )
    parser.add_argument("input", type=Path, help="Archivo MP4 o directorio local de MP4")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Directorio de salidas")
    parser.add_argument("--model", default="large-v3-turbo", help="Modelo local (predeterminado: large-v3-turbo)")
    parser.add_argument("--language", default=None, help="Idioma ISO, por ejemplo es o en; omite para auto")
    parser.add_argument("--device", choices=DEVICE_CHOICES, default="auto")
    parser.add_argument("--compute-type", choices=COMPUTE_TYPE_CHOICES, default="auto")
    parser.add_argument("--no-vad", action="store_true", help="Desactiva el filtro VAD")
    parser.add_argument("--word-timestamps", action="store_true", help="Incluye timestamps por palabra en JSON")
    parser.add_argument("--overwrite", action="store_true", help="Permite sustituir salidas de la misma llamada")
    parser.add_argument("--model-cache", type=Path, default=None, help="Directorio local de cache de modelos")
    return parser


def main(argv: list[str] | None = None, application: TranscriptionApplication | None = None) -> int:
    """Ejecuta el contrato CLI y devuelve 0, 2 o 3; no importa dependencias GUI."""
    args = build_parser().parse_args(argv)
    request = TranscriptionRequest(
        input_path=args.input,
        output_dir=args.output_dir,
        model=args.model,
        language=args.language,
        device=args.device,
        compute_type=args.compute_type,
        vad=not args.no_vad,
        word_timestamps=args.word_timestamps,
        overwrite=args.overwrite,
        model_cache=args.model_cache,
    )
    try:
        run = (application or TranscriptionApplication()).run(request)
        if isinstance(run, FolderTranscriptionRun):
            for result in run.results:
                print(f"{result.status.upper()}: {result.source.name} — {result.detail}")
            successes = sum(item.status == "success" for item in run.results)
            failures = sum(item.status == "error" for item in run.results)
            skipped = sum(item.status == "skipped" for item in run.results)
            print(f"Resumen: {successes} éxito(s), {failures} error(es), {skipped} omitido(s).")
            return 3 if failures else 0
    except InputValidationError as error:
        print(f"Error de entrada: {error}")
        return 2
    except RuntimeError as error:
        print(f"Error de transcripción: {error}")
        return 3
    assert isinstance(run, FileTranscriptionRun)
    outputs = run.outputs
    print(f"TXT: {outputs.txt}")
    print(f"JSON: {outputs.json}")
    print(f"SRT: {outputs.srt}")
    print(f"VTT: {outputs.vtt}")
    return 0
