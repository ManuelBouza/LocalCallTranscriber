from pathlib import Path

from local_call_transcriber.domain import TranscriptResult
from local_call_transcriber.orchestration import transcribe_folder


class StubEngine:
    def transcribe(self, media_path: Path, **_: object) -> TranscriptResult:
        if media_path.name == "bad.mp4":
            raise RuntimeError("modelo no disponible")
        return TranscriptResult(model="stub", language="es", segments=())


def test_folder_continues_after_errors_and_skips_existing_output(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    for name in ("good.mp4", "bad.mp4", "existing.mp4"):
        (input_dir / name).write_bytes(b"placeholder")
    output_dir.mkdir()
    (output_dir / "existing.txt").write_text("previous", encoding="utf-8")

    results = transcribe_folder(StubEngine(), input_dir, output_dir, None, True, False, False)

    assert [item.status for item in results] == ["error", "skipped", "success"]
    assert (output_dir / "good.json").is_file()
    assert "bad.mp4" in (output_dir / "folder-run.jsonl").read_text(encoding="utf-8")
