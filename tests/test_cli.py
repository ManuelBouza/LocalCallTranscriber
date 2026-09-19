from pathlib import Path

from local_call_transcriber.cli import main


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
