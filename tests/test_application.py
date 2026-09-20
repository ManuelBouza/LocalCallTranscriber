"""Pruebas de la capa compartida, sin motor, modelo ni dependencias GUI."""

from pathlib import Path

from local_call_transcriber.application import (
    FileTranscriptionRun,
    TranscriptionApplication,
    TranscriptionRequest,
)
from local_call_transcriber.domain import TranscriptResult, TranscriptSegment


class StubEngine:
    def transcribe(self, media_path: Path, **_: object) -> TranscriptResult:
        return TranscriptResult(
            model="stub", language="es", segments=(TranscriptSegment(0, 1, "Texto local"),)
        )


def test_application_runs_fixture_and_exposes_the_txt_path(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.mp4"
    fixture.write_bytes(b"fixture local")
    request = TranscriptionRequest(input_path=fixture, output_dir=tmp_path / "results")

    run = TranscriptionApplication(lambda _: StubEngine()).run(request)

    assert isinstance(run, FileTranscriptionRun)
    assert run.outputs.txt == tmp_path / "results" / "fixture.txt"
    assert run.outputs.txt.read_text(encoding="utf-8") == "Texto local\n"


def test_application_request_contains_cli_and_future_gui_options(tmp_path: Path) -> None:
    request = TranscriptionRequest(
        input_path=tmp_path / "call.mp4",
        output_dir=tmp_path / "out",
        model="large-v3",
        language="en",
        device="cpu",
        compute_type="int8",
        vad=False,
        word_timestamps=True,
        overwrite=True,
    )

    assert request.model == "large-v3"
    assert request.word_timestamps is True
    assert request.vad is False
