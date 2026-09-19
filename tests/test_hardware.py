"""Pruebas del selector de CPU/CUDA sin requerir una GPU en la suite."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from local_call_transcriber.engines.faster_whisper import FasterWhisperEngine


class FakeModel:
    attempts: list[tuple[str, str]] = []
    fail_cuda = False

    def __init__(self, _name: str, *, device: str, compute_type: str, download_root: str) -> None:
        del download_root
        self.attempts.append((device, compute_type))
        if device == "cuda" and self.fail_cuda:
            raise OSError("DLL CUDA ausente")

    def transcribe(self, *_args: object, **_kwargs: object) -> tuple[list[object], object]:
        return [], SimpleNamespace(language="es")


@pytest.fixture(autouse=True)
def fake_faster_whisper(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeModel.attempts = []
    FakeModel.fail_cuda = False
    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=FakeModel))


def test_cpu_keeps_validated_int8_path(tmp_path: Path) -> None:
    engine = FasterWhisperEngine("tiny", tmp_path / "models", device="cpu", compute_type="auto")

    engine.transcribe(tmp_path / "call.mp4", None, True, False)

    assert FakeModel.attempts == [("cpu", "int8")]


def test_cuda_failure_is_explicit_and_actionable(tmp_path: Path) -> None:
    FakeModel.fail_cuda = True
    engine = FasterWhisperEngine("tiny", tmp_path / "models", device="cuda", compute_type="float16")

    with pytest.raises(RuntimeError, match=r"doctor\.ps1.*cuDNN 9"):
        engine.transcribe(tmp_path / "call.mp4", None, True, False)


def test_auto_falls_back_to_cpu_when_cuda_initialization_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    FakeModel.fail_cuda = True
    engine = FasterWhisperEngine("tiny", tmp_path / "models", device="auto", compute_type="auto")

    engine.transcribe(tmp_path / "call.mp4", None, True, False)

    assert FakeModel.attempts == [("cuda", "float16"), ("cpu", "int8")]
    assert "Se usará CPU con int8" in capsys.readouterr().out


@pytest.mark.parametrize("compute_type", ["float16", "int8_float16"])
def test_cuda_accepts_selected_compute_types(tmp_path: Path, compute_type: str) -> None:
    engine = FasterWhisperEngine("tiny", tmp_path / "models", device="cuda", compute_type=compute_type)

    engine.transcribe(tmp_path / "call.mp4", None, True, False)

    assert FakeModel.attempts == [("cuda", compute_type)]
