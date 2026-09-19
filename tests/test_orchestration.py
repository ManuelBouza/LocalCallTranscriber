import json
from pathlib import Path

import pytest

from local_call_transcriber.domain import TranscriptResult, TranscriptSegment
from local_call_transcriber.orchestration import InputValidationError, transcribe_file


class StubEngine:
    def transcribe(self, media_path: Path, language: str | None, vad: bool) -> TranscriptResult:
        return TranscriptResult(
            model="stub", language=language or "es", segments=(TranscriptSegment(0.0, 1.5, "Hola"),)
        )


def test_transcribe_file_writes_txt_and_json(tmp_path: Path) -> None:
    media = tmp_path / "call.mp4"
    media.write_bytes(b"placeholder")

    outputs = transcribe_file(StubEngine(), media, tmp_path / "out", "es", True)

    assert outputs.txt.read_text(encoding="utf-8") == "Hola\n"
    payload = json.loads(outputs.json.read_text(encoding="utf-8"))
    assert payload["model"] == "stub"
    assert payload["language"] == "es"
    assert payload["segments"] == [{"start": 0.0, "end": 1.5, "text": "Hola"}]


@pytest.mark.parametrize("name", ["missing.mp4", "call.wav"])
def test_transcribe_file_rejects_missing_or_non_mp4(tmp_path: Path, name: str) -> None:
    media = tmp_path / name
    if media.suffix == ".wav":
        media.write_bytes(b"placeholder")

    with pytest.raises(InputValidationError):
        transcribe_file(StubEngine(), media, tmp_path / "out", None, True)
