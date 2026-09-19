import json
from pathlib import Path

import pytest

from local_call_transcriber.domain import TranscriptResult, TranscriptSegment, TranscriptWord
from local_call_transcriber.orchestration import InputValidationError, transcribe_file


class StubEngine:
    def __init__(self) -> None:
        self.last_word_timestamps: bool | None = None

    def transcribe(
        self, media_path: Path, language: str | None, vad: bool, word_timestamps: bool
    ) -> TranscriptResult:
        self.last_word_timestamps = word_timestamps
        return TranscriptResult(
            model="stub",
            language=language or "es",
            segments=(
                TranscriptSegment(
                    2.0, 3.5, "Segundo", (TranscriptWord(2.0, 2.5, "Segundo"),)
                ),
                TranscriptSegment(0.0, 1.5, "Hola", (TranscriptWord(0.0, 0.4, "Hola"),)),
            ),
        )


def test_transcribe_file_writes_txt_and_json(tmp_path: Path) -> None:
    media = tmp_path / "call.mp4"
    media.write_bytes(b"placeholder")

    engine = StubEngine()
    outputs = transcribe_file(engine, media, tmp_path / "out", "es", True, True, False)

    assert engine.last_word_timestamps is True
    assert outputs.txt.read_text(encoding="utf-8") == "Hola\nSegundo\n"
    payload = json.loads(outputs.json.read_text(encoding="utf-8"))
    assert payload["model"] == "stub"
    assert payload["language"] == "es"
    assert [segment["text"] for segment in payload["segments"]] == ["Hola", "Segundo"]
    assert payload["segments"][0]["words"] == [{"start": 0.0, "end": 0.4, "text": "Hola"}]
    assert outputs.srt.read_text(encoding="utf-8") == (
        "1\n00:00:00,000 --> 00:00:01,500\nHola\n\n2\n00:00:02,000 --> 00:00:03,500\nSegundo\n"
    )
    assert outputs.vtt.read_text(encoding="utf-8") == (
        "WEBVTT\n\n00:00:00.000 --> 00:00:01.500\nHola\n\n00:00:02.000 --> 00:00:03.500\nSegundo\n"
    )


@pytest.mark.parametrize("name", ["missing.mp4", "call.wav"])
def test_transcribe_file_rejects_missing_or_non_mp4(tmp_path: Path, name: str) -> None:
    media = tmp_path / name
    if media.suffix == ".wav":
        media.write_bytes(b"placeholder")

    with pytest.raises(InputValidationError):
        transcribe_file(StubEngine(), media, tmp_path / "out", None, True, False, False)


def test_transcribe_file_refuses_existing_outputs_without_overwrite(tmp_path: Path) -> None:
    media = tmp_path / "call.mp4"
    media.write_bytes(b"placeholder")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    existing = output_dir / "call.txt"
    existing.write_text("preserve", encoding="utf-8")

    with pytest.raises(InputValidationError, match="--overwrite"):
        transcribe_file(StubEngine(), media, output_dir, None, True, False, False)
    assert existing.read_text(encoding="utf-8") == "preserve"


def test_transcribe_file_can_disable_word_timestamps(tmp_path: Path) -> None:
    media = tmp_path / "call.mp4"
    media.write_bytes(b"placeholder")
    engine = StubEngine()

    transcribe_file(engine, media, tmp_path / "out", None, True, False, False)

    assert engine.last_word_timestamps is False
