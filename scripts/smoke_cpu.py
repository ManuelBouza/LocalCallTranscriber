"""Smoke test local de la ruta CPU, sin archivos multimedia versionados."""

import json
import os
import tempfile
from pathlib import Path

import av
import numpy as np

from local_call_transcriber.cli import main


def create_silent_mp4(destination: Path) -> None:
    container = av.open(str(destination), mode="w")
    stream = container.add_stream("aac", rate=16_000)
    stream.layout = "mono"
    for _ in range(16):
        frame = av.AudioFrame.from_ndarray(np.zeros((1, 1024), dtype=np.int16), format="s16", layout="mono")
        frame.sample_rate = 16_000
        for packet in stream.encode(frame):
            container.mux(packet)
    for packet in stream.encode(None):
        container.mux(packet)
    container.close()


def main_smoke() -> int:
    cache_root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "LocalCallTranscriber" / "models"
    with tempfile.TemporaryDirectory(prefix="local-call-transcriber-smoke-") as temporary_directory:
        temporary_path = Path(temporary_directory)
        source = temporary_path / "smoke.mp4"
        output_dir = temporary_path / "output"
        create_silent_mp4(source)
        exit_code = main(
            [
                str(source),
                "--output-dir",
                str(output_dir),
                "--model",
                "tiny",
                "--device",
                "cpu",
                "--compute-type",
                "int8",
                "--model-cache",
                str(cache_root),
            ]
        )
        if exit_code != 0:
            return exit_code
        payload = json.loads((output_dir / "smoke.json").read_text(encoding="utf-8"))
        required_keys = {"model", "language", "segments"}
        if not required_keys.issubset(payload) or not (output_dir / "smoke.txt").is_file():
            raise RuntimeError("El smoke test no generó salidas TXT y JSON válidas.")
    print("PASS: smoke test CPU completado con un MP4 temporal y PyAV.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_smoke())
