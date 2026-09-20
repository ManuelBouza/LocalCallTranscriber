"""Pruebas de la capa Qt; se omiten si se valida sólo el runtime CLI."""
# ruff: noqa: E402

import os
import time
from pathlib import Path
from threading import Event

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PySide6 = pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from local_call_transcriber.application import TranscriptionApplication
from local_call_transcriber.domain import TranscriptResult, TranscriptSegment
from local_call_transcriber.gui.main_window import MainWindow


class StubEngine:
    def transcribe(self, media_path: Path, **_: object) -> TranscriptResult:
        return TranscriptResult(
            model="stub",
            language="es",
            segments=(TranscriptSegment(0, 1, "Texto GUI"),),
        )


class BlockingEngine:
    def __init__(self) -> None:
        self.started = Event()
        self.release = Event()
        self.calls: list[str] = []

    def transcribe(self, media_path: Path, **_: object) -> TranscriptResult:
        self.calls.append(media_path.name)
        self.started.set()
        if not self.release.wait(3):
            raise RuntimeError("timeout de la prueba")
        return TranscriptResult(
            model="stub",
            language="es",
            segments=(TranscriptSegment(0, 1, f"Texto {media_path.stem}"),),
        )


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def wait_until(
    qapp: QApplication,
    predicate: object,
    timeout: float = 3.0,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qapp.processEvents()
        if predicate():  # type: ignore[operator]
            return
        time.sleep(0.01)
    qapp.processEvents()
    assert predicate()  # type: ignore[operator]


def test_gui_translates_all_simple_controls_to_core_request(
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    window = MainWindow()
    window.input_path_edit.setText(str(tmp_path / "call.mp4"))
    window.output_dir_edit.setText(str(tmp_path / "out"))

    auto_request = window.build_request()
    assert (auto_request.device, auto_request.compute_type) == ("auto", "auto")

    window.profile_combo.setCurrentText("Calidad")
    window.language_combo.setCurrentText("Inglés")
    window.hardware_combo.setCurrentText("CPU")
    window.vad_checkbox.setChecked(False)
    window.word_timestamps_checkbox.setChecked(True)
    window.overwrite_checkbox.setChecked(True)

    request = window.build_request()

    assert request.model == "large-v3"
    assert request.language == "en"
    assert (request.device, request.compute_type) == ("cpu", "int8")
    assert request.vad is False
    assert request.word_timestamps is True
    assert request.overwrite is True


def test_gui_runs_shared_application_in_background(
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "call.mp4"
    fixture.write_bytes(b"fixture local")
    output_dir = tmp_path / "results"
    engine = BlockingEngine()
    window = MainWindow(TranscriptionApplication(lambda _: engine))
    window.input_path_edit.setText(str(fixture))
    window.output_dir_edit.setText(str(output_dir))

    started_at = time.monotonic()
    window.transcribe()
    elapsed = time.monotonic() - started_at

    assert elapsed < 0.5
    assert engine.started.wait(1)
    assert window.is_running is True
    assert window.transcribe_button.isEnabled() is False

    engine.release.set()
    wait_until(qapp, lambda: not window.is_running)

    assert (output_dir / "call.txt").read_text(encoding="utf-8") == "Texto call\n"
    assert "COMPLETADO" in window.log_view.toPlainText()
    assert window.progress_bar.value() == 1


def test_gui_shows_folder_summary_and_file_progress(
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "incoming"
    input_dir.mkdir()
    for name in ("a.mp4", "b.mp4"):
        (input_dir / name).write_bytes(b"fixture local")

    window = MainWindow(TranscriptionApplication(lambda _: StubEngine()))
    window.input_path_edit.setText(str(input_dir))
    window.output_dir_edit.setText(str(tmp_path / "results"))

    window.transcribe()
    wait_until(qapp, lambda: not window.is_running)

    assert "Carpeta completada: 2 éxito(s)" in window.status_label.text()
    assert window.progress_bar.maximum() == 2
    assert window.progress_bar.value() == 2
    assert "SUCCESS 2/2" in window.log_view.toPlainText()


def test_gui_cancellation_finishes_current_file_and_stops_before_next(
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "incoming"
    input_dir.mkdir()
    for name in ("a.mp4", "b.mp4"):
        (input_dir / name).write_bytes(b"fixture local")

    output_dir = tmp_path / "results"
    engine = BlockingEngine()
    window = MainWindow(TranscriptionApplication(lambda _: engine))
    window.input_path_edit.setText(str(input_dir))
    window.output_dir_edit.setText(str(output_dir))

    window.transcribe()
    assert engine.started.wait(1)

    window.cancel_current_run()
    engine.release.set()
    wait_until(qapp, lambda: not window.is_running)

    assert engine.calls == ["a.mp4"]
    assert (output_dir / "a.txt").is_file()
    assert not (output_dir / "b.txt").exists()
    assert "Cancelado después del archivo actual: 1/2" in window.status_label.text()
    assert "CANCELADO" in window.log_view.toPlainText()


def test_gui_shows_actionable_error_for_missing_paths(qapp: QApplication) -> None:
    window = MainWindow()

    window.transcribe()

    assert "Selecciona un archivo MP4" in window.status_label.text()
    assert window.is_running is False


def test_gui_reports_engine_error_without_blocking(
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    class FailingEngine:
        def transcribe(self, media_path: Path, **_: object) -> TranscriptResult:
            raise RuntimeError("modelo no disponible")

    fixture = tmp_path / "call.mp4"
    fixture.write_bytes(b"fixture")
    window = MainWindow(TranscriptionApplication(lambda _: FailingEngine()))
    window.input_path_edit.setText(str(fixture))
    window.output_dir_edit.setText(str(tmp_path / "results"))

    window.transcribe()
    wait_until(qapp, lambda: not window.is_running)

    assert "modelo no disponible" in window.status_label.text()
    assert "ERROR" in window.log_view.toPlainText()
