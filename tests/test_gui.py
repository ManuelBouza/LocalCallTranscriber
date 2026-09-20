"""Pruebas de la capa Qt; se omiten si se valida sólo el runtime CLI."""
# ruff: noqa: E402

import os
from pathlib import Path

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
            model="stub", language="es", segments=(TranscriptSegment(0, 1, "Texto GUI"),)
        )


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_gui_translates_all_simple_controls_to_core_request(qapp: QApplication, tmp_path: Path) -> None:
    window = MainWindow()
    window.input_path_edit.setText(str(tmp_path / "call.mp4"))
    window.output_dir_edit.setText(str(tmp_path / "out"))
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


def test_gui_runs_shared_application_and_shows_txt_result(qapp: QApplication, tmp_path: Path) -> None:
    fixture = tmp_path / "call.mp4"
    fixture.write_bytes(b"fixture local")
    output_dir = tmp_path / "results"
    window = MainWindow(TranscriptionApplication(lambda _: StubEngine()))
    window.input_path_edit.setText(str(fixture))
    window.output_dir_edit.setText(str(output_dir))

    window.transcribe()

    assert (output_dir / "call.txt").read_text(encoding="utf-8") == "Texto GUI\n"
    assert str(output_dir / "call.txt") in window.status_label.text()


def test_gui_shows_folder_summary(qapp: QApplication, tmp_path: Path) -> None:
    input_dir = tmp_path / "incoming"
    input_dir.mkdir()
    (input_dir / "call.mp4").write_bytes(b"fixture local")
    window = MainWindow(TranscriptionApplication(lambda _: StubEngine()))
    window.input_path_edit.setText(str(input_dir))
    window.output_dir_edit.setText(str(tmp_path / "results"))

    window.transcribe()

    assert "Carpeta completada: 1 éxito(s)" in window.status_label.text()


def test_gui_shows_actionable_error_for_missing_paths(qapp: QApplication) -> None:
    window = MainWindow()

    window.transcribe()

    assert "Selecciona un archivo MP4" in window.status_label.text()
