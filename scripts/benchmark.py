"""Benchmark local reproducible de faster-whisper; no versiona fixture ni resultados."""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import av

from local_call_transcriber.hardware import prepare_cuda_runtime
from smoke_cpu import create_silent_mp4


def media_duration_seconds(media_path: Path) -> float:
    container = av.open(str(media_path))
    try:
        stream = next(stream for stream in container.streams if stream.type == "audio")
        if stream.duration is None or stream.time_base is None:
            raise RuntimeError("La fixture no contiene una duración de audio válida.")
        return float(stream.duration * stream.time_base)
    finally:
        container.close()


def vram_mib() -> int | None:
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=used_memory", "--format=csv,noheader,nounits"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    values = [line.strip() for line in result.stdout.splitlines() if line.strip().isdigit()]
    return sum(int(value) for value in values) if values else 0


def rss_mib() -> float:
    import ctypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("data", ctypes.c_byte * 64)]

    counters = Counters()
    counters.cb = ctypes.sizeof(Counters)
    process = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
        return 0.0
    working_set_offset = 8 if ctypes.sizeof(ctypes.c_void_p) == 4 else 16
    working_set = int.from_bytes(bytes(counters.data[working_set_offset : working_set_offset + 8]), "little")
    return round(working_set / 1024 / 1024, 2)


def run_case(media_path: Path, cache: Path, model_name: str, device: str, compute_type: str, batch_size: int) -> dict[str, object]:
    if device == "cuda":
        prepare_cuda_runtime()
    from faster_whisper import BatchedInferencePipeline, WhisperModel

    duration = media_duration_seconds(media_path)
    started = time.perf_counter()
    model = WhisperModel(model_name, device=device, compute_type=compute_type, download_root=str(cache))
    loaded = time.perf_counter()
    pipeline = BatchedInferencePipeline(model=model)
    segments, info = pipeline.transcribe(str(media_path), batch_size=batch_size, vad_filter=True)
    materialized = list(segments)
    finished = time.perf_counter()
    transcription_seconds = finished - loaded
    return {
        "status": "PASS",
        "model": model_name,
        "device": device,
        "compute_type": compute_type,
        "batch_size": batch_size,
        "audio_duration_seconds": round(duration, 3),
        "model_load_seconds": round(loaded - started, 3),
        "transcription_seconds": round(transcription_seconds, 3),
        "total_seconds": round(finished - started, 3),
        "real_time_factor": round(transcription_seconds / duration, 3),
        "ram_working_set_mib": rss_mib(),
        "vram_mib_after": vram_mib(),
        "segments": len(materialized),
        "detected_language": getattr(info, "language", None),
        "quality_observation": "Fixture controlada sin habla: se esperaban y obtuvieron 0 segmentos.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark local de CPU/CUDA para faster-whisper.")
    parser.add_argument("--output", type=Path, required=True, help="JSON de resultados, fuera de Git")
    parser.add_argument("--model-cache", type=Path, required=True)
    args = parser.parse_args()
    cases = [(model, "cpu", "int8", 1) for model in ("large-v3", "large-v3-turbo")]
    cases += [
        (model, "cuda", compute, batch)
        for model in ("large-v3", "large-v3-turbo")
        for compute in ("float16", "int8_float16")
        for batch in (1, 4)
    ]
    temporary_directory = Path(tempfile.mkdtemp(prefix="local-call-transcriber-benchmark-"))
    try:
        media_path = temporary_directory / "controlled-silence.mp4"
        create_silent_mp4(media_path)
        results: list[dict[str, object]] = []
        for model, device, compute_type, batch_size in cases:
            try:
                results.append(run_case(media_path, args.model_cache, model, device, compute_type, batch_size))
            except Exception as error:
                results.append({"status": "FAIL", "model": model, "device": device, "compute_type": compute_type, "batch_size": batch_size, "error": str(error)})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"fixture": "silencio local generado", "results": results}, indent=2), encoding="utf-8")
    finally:
        shutil.rmtree(temporary_directory, ignore_errors=True)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
