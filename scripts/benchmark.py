"""Benchmark que invoca la misma CLI usada por producción."""

import argparse
import json
import shutil
import tempfile
import time
from pathlib import Path
import av
from local_call_transcriber.cli import main as cli_main


def duration(path: Path) -> float:
    c = av.open(str(path))
    try:
        s = next(x for x in c.streams if x.type == "audio")
        return float(s.duration * s.time_base)
    finally:
        c.close()


def wav_to_mp4(source: Path, destination: Path) -> None:
    source_c, dest_c = av.open(str(source)), av.open(str(destination), "w")
    try:
        stream = next(x for x in source_c.streams if x.type == "audio")
        output = dest_c.add_stream("aac", rate=16000)
        output.layout = "mono"
        resampler = av.AudioResampler(format="fltp", layout="mono", rate=16000)
        for frame in source_c.decode(stream):
            for converted in resampler.resample(frame):
                for packet in output.encode(converted):
                    dest_c.mux(packet)
        for packet in output.encode(None):
            dest_c.mux(packet)
    finally:
        source_c.close()
        dest_c.close()


def overlap(text: str, reference: str | None) -> float | None:
    if not reference:
        return None
    expected, actual = set(reference.casefold().split()), set(text.casefold().split())
    return round(len(expected & actual) / len(expected), 3) if expected else None


def run_case(
    source: Path, cache: Path, model: str, device: str, compute: str, reference: str | None
) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="lct-benchmark-output-") as tmp:
        output = Path(tmp)
        started = time.perf_counter()
        code = cli_main(
            [
                str(source),
                "--output-dir",
                str(output),
                "--model",
                model,
                "--device",
                device,
                "--compute-type",
                compute,
                "--model-cache",
                str(cache),
            ]
        )
        elapsed = time.perf_counter() - started
        transcript = (
            (output / f"{source.stem}.txt").read_text(encoding="utf-8") if code == 0 else ""
        )
    seconds = duration(source)
    return {
        "path": "production-cli",
        "status": "PASS" if code == 0 else "FAIL",
        "model": model,
        "device": device,
        "compute_type": compute,
        "audio_duration_seconds": round(seconds, 3),
        "total_seconds": round(elapsed, 3),
        "real_time_factor": round(elapsed / seconds, 3),
        "segment_count": len([x for x in transcript.splitlines() if x.strip()]),
        "quality_observation": "Comparación cualitativa con referencia local.",
        "reference_token_overlap": overlap(transcript, reference),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, action="append", default=[])
    p.add_argument("--controlled-speech-wav", type=Path)
    p.add_argument("--reference-text")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--model-cache", type=Path, required=True)
    a = p.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="lct-benchmark-media-"))
    try:
        inputs = list(a.input)
        if a.controlled_speech_wav:
            mp4 = tmp / "controlled-speech.mp4"
            wav_to_mp4(a.controlled_speech_wav, mp4)
            inputs.append(mp4)
        if not inputs:
            raise SystemExit("Indica --input MP4 o --controlled-speech-wav WAV.")
        cases = [(m, "cpu", "int8") for m in ("large-v3", "large-v3-turbo")] + [
            (m, "cuda", c)
            for m in ("large-v3", "large-v3-turbo")
            for c in ("float16", "int8_float16")
        ]
        results = []
        for source in inputs:
            for model, device, compute in cases:
                try:
                    results.append(
                        run_case(source, a.model_cache, model, device, compute, a.reference_text)
                    )
                except Exception as error:
                    results.append(
                        {
                            "path": "production-cli",
                            "status": "FAIL",
                            "model": model,
                            "device": device,
                            "compute_type": compute,
                            "error": str(error),
                        }
                    )
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(a.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
