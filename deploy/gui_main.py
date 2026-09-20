"""Entrypoint usado exclusivamente para construir y validar el paquete Windows."""

import json
import sys
import tempfile
from pathlib import Path

import av
import numpy as np

from local_call_transcriber.application import (
    FileTranscriptionRun,
    TranscriptionApplication,
    TranscriptionRequest,
)
from local_call_transcriber.gui.__main__ import main as gui_main


def _create_silent_mp4(destination: Path) -> None:
    """Genera una fixture temporal local sin versionar multimedia."""
    container = av.open(str(destination), mode="w")
    stream = container.add_stream("aac", rate=16_000)
    stream.layout = "mono"
    for _ in range(16):
        frame = av.AudioFrame.from_ndarray(
            np.zeros((1, 1024), dtype=np.int16),
            format="s16",
            layout="mono",
        )
        frame.sample_rate = 16_000
        for packet in stream.encode(frame):
            container.mux(packet)
    for packet in stream.encode(None):
        container.mux(packet)
    container.close()


def package_smoke() -> int:
    """Valida dentro del paquete la ruta CPU real y los cuatro outputs."""
    with tempfile.TemporaryDirectory(
        prefix="local-call-transcriber-package-smoke-"
    ) as temporary_directory:
        root = Path(temporary_directory)
        source = root / "smoke.mp4"
        output_dir = root / "output"
        _create_silent_mp4(source)

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
