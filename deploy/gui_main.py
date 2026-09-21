"""Entrypoint usado exclusivamente para construir y validar el paquete Windows."""

import json
import os
import sys
import tempfile
from pathlib import Path

from local_call_transcriber.application import (
    FileTranscriptionRun,
    TranscriptionApplication,
    TranscriptionRequest,
)
from local_call_transcriber.gui.__main__ import main as gui_main

PACKAGE_SMOKE_INPUT_ENV = "LOCALCALLTRANSCRIBER_PACKAGE_SMOKE_INPUT"


def package_smoke() -> int:
    """Valida dentro del paquete la ruta CPU real usando un MP4 creado externamente."""
    source_value = os.environ.get(PACKAGE_SMOKE_INPUT_ENV)
    if not source_value:
        raise RuntimeError(
            f"Falta {PACKAGE_SMOKE_INPUT_ENV}; el fixture del smoke debe generarse fuera del paquete."
        )

    source = Path(source_value)
    if not source.is_file():
        raise RuntimeError(f"No existe el MP4 del package smoke: {source}")

    with tempfile.TemporaryDirectory(
        prefix="local-call-transcriber-package-smoke-"
    ) as temporary_directory:
        output_dir = Path(temporary_directory) / "output"

        run = TranscriptionApplication().run(
            TranscriptionRequest(
                input_path=source,
                output_dir=output_dir,
                model="tiny",
                device="cpu",
                compute_type="int8",
            )
        )
        if not isinstance(run, FileTranscriptionRun):
            raise RuntimeError("El smoke empaquetado no devolvió un resultado de archivo.")

        for path in (
            run.outputs.txt,
            run.outputs.json,
            run.outputs.srt,
            run.outputs.vtt,
        ):
            if not path.is_file():
                raise RuntimeError(f"Falta una salida del smoke empaquetado: {path.name}")

        payload = json.loads(run.outputs.json.read_text(encoding="utf-8"))
        if payload.get("model") != "tiny" or "segments" not in payload:
            raise RuntimeError("El JSON del smoke empaquetado no es válido.")

    return 0


if __name__ == "__main__":
    if "--package-smoke" in sys.argv:
        raise SystemExit(package_smoke())
    raise SystemExit(gui_main())
