"""Genera fuera del paquete el MP4 temporal usado por el package smoke."""

import argparse
from pathlib import Path

import av
import numpy as np


def create_silent_mp4(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    container = av.open(str(destination), mode="w")
    try:
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
    finally:
        container.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    create_silent_mp4(args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
