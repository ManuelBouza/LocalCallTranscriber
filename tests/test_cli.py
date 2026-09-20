import importlib.metadata
import sys
from pathlib import Path

from local_call_transcriber.application import TranscriptionApplication
from local_call_transcriber.domain import TranscriptResult, TranscriptSegment
from local_call_transcriber.cli import main


class StubEngine:
    def transcribe(self, media_path: Path, **_: object) -> TranscriptResult:
        return TranscriptResult(
            model="stub", language="es", segments=(TranscriptSegment(0, 1, "Texto fixture"),)
        )


def test_cli_returns_clear_error_for_missing_input(tmp_path: Path, capsys: object) -> None:
    exit_code = main([str(tmp_path / "missing.mp4")])

    assert exit_code == 2
    assert "No existe el archivo de entrada" in capsys.readouterr().out


def test_cli_returns_clear_error_for_unsupported_format(tmp_path: Path, capsys: object) -> None:
    source = tmp_path / "call.wav"
    source.write_bytes(b"not mp4")

    exit_code = main([str(source)])

    assert exit_code == 2
    assert "únicamente archivos MP4" in capsys.readouterr().out


def test_cli_help_documents_supported_automation_options(capsys: object) -> None:
    try:
        main(["--help"])
    except SystemExit as error:
        assert error.code == 0

    help_text = capsys.readouterr().out
    for option in ("--output-dir", "--device", "--compute-type", "--word-timestamps", "--overwrite"):
        assert option in help_text


def test_cli_documented_file_flow_creates_locatable_txt(tmp_path: Path, capsys: object) -> None:
    fixture = tmp_path / "call-001.mp4"
    fixture.write_bytes(b"fixture local")
    output_dir = tmp_path / "transcripts"

    exit_code = main(
        [str(fixture), "--output-dir", str(output_dir)],
        application=TranscriptionApplication(lambda _: StubEngine()),
    )

    assert exit_code == 0
    assert (output_dir / "call-001.txt").read_text(encoding="utf-8") == "Texto fixture\n"
    assert f"TXT: {output_dir / 'call-001.txt'}" in capsys.readouterr().out


def test_nominal_entry_point_is_declared_and_cli_does_not_import_gui() -> None:
    entry_points = importlib.metadata.entry_points(group="console_scripts")

    assert any(point.name == "local-call-transcriber" for point in entry_points)
    assert "PySide6" not in sys.modules
