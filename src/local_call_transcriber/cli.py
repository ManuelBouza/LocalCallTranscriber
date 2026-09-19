"""CLI inicial de transcripción local CPU."""

import argparse
import os
from pathlib import Path

from local_call_transcriber.engines.faster_whisper import FasterWhisperEngine
from local_call_transcriber.orchestration import InputValidationError, transcribe_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Transcribe un MP4 local en CPU con faster-whisper.")
    parser.add_argument("input", type=Path, help="Archivo MP4 local")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--model", default="tiny", help="Modelo faster-whisper a descargar localmente")
    parser.add_argument("--language", default=None, help="Idioma ISO, por ejemplo es o en; omite para auto")
    parser.add_argument("--device", choices=["cpu"], default="cpu")
    parser.add_argument("--compute-type", choices=["int8"], default="int8")
    parser.add_argument("--no-vad", action="store_true", help="Desactiva el filtro VAD")
    parser.add_argument("--model-cache", type=Path, default=None)
    return parser


def default_model_cache() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "LocalCallTranscriber" / "models"
    return Path.home() / ".cache" / "LocalCallTranscriber" / "models"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cache = args.model_cache or default_model_cache()
    engine = FasterWhisperEngine(model_name=args.model, model_cache=cache, compute_type=args.compute_type)
    try:
        outputs = transcribe_file(
            engine=engine,
            media_path=args.input,
            output_dir=args.output_dir,
            language=args.language,
            vad=not args.no_vad,
        )
    except InputValidationError as error:
        print(f"Error de entrada: {error}")
        return 2
    except RuntimeError as error:
        print(f"Error de transcripción: {error}")
        return 3
    print(f"TXT: {outputs.txt}")
    print(f"JSON: {outputs.json}")
    return 0
