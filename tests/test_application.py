"""Pruebas de la capa compartida, sin motor, modelo ni dependencias GUI."""

from pathlib import Path

from local_call_transcriber.application import (
    FileTranscriptionRun,
    FolderTranscriptionRun,
    TranscriptionApplication,
    TranscriptionRequest,
)
from local_call_transcriber.domain import TranscriptResult, TranscriptSegment
from local_call_transcriber.orchestration import FolderItemResult


class StubEngine:
    def transcribe(self, media_path: Path, **_: object) -> TranscriptResult:
        return TranscriptResult(
            model="stub",
            language="es",
            segments=(TranscriptSegment(0, 1, "Texto local"),),
        )


def test_application_runs_fixture_and_exposes_the_txt_path(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.mp4"
    fixture.write_bytes(b"fixture local")
    request = TranscriptionRequest(
        input_path=fixture,
        output_dir=tmp_path / "results",
    )

    run = TranscriptionApplication(lambda _: StubEngine()).run(request)

    assert isinstance(run, FileTranscriptionRun)
    assert run.outputs.txt == tmp_path / "results" / "fixture.txt"
    assert run.outputs.txt.read_text(encoding="utf-8") == "Texto local\n"


def test_application_request_contains_cli_and_future_gui_options(
    tmp_path: Path,
) -> None:
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


def test_application_reports_progress_and_cancels_between_folder_items(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "incoming"
    input_dir.mkdir()
    for name in ("a.mp4", "b.mp4"):
        (input_dir / name).write_bytes(b"fixture")

    started: list[str] = []
    finished: list[str] = []
    cancellation = {"requested": False}

    def on_started(path: Path, index: int, total: int) -> None:
        assert total == 2
        assert index >= 1
        started.append(path.name)

    def on_finished(item: FolderItemResult, index: int, total: int) -> None:
        assert total == 2
        assert index == 1
        finished.append(item.source.name)
        cancellation["requested"] = True

    run = TranscriptionApplication(lambda _: StubEngine()).run(
        TranscriptionRequest(
            input_path=input_dir,
            output_dir=tmp_path / "out",
        ),
        on_item_started=on_started,
        on_item_finished=on_finished,
        should_cancel=lambda: cancellation["requested"],
    )

    assert isinstance(run, FolderTranscriptionRun)
    assert run.cancelled is True
    assert run.total == 2
    assert started == ["a.mp4"]
    assert finished == ["a.mp4"]
    assert (tmp_path / "out" / "a.txt").is_file()
    assert not (tmp_path / "out" / "b.txt").exists()
