"""Adaptador CPU de faster-whisper."""

from pathlib import Path

from local_call_transcriber.domain import TranscriptResult, TranscriptSegment, TranscriptWord


class FasterWhisperEngine:
    def __init__(self, model_name: str, model_cache: Path, compute_type: str = "int8") -> None:
        self._model_name = model_name
        self._model_cache = model_cache
        self._compute_type = compute_type

    def transcribe(
        self, media_path: Path, language: str | None, vad: bool, word_timestamps: bool
    ) -> TranscriptResult:
        try:
            from faster_whisper import WhisperModel
        except ImportError as error:
            raise RuntimeError(
                "faster-whisper no está instalado en .venv. Ejecuta .\\scripts\\bootstrap.ps1."
            ) from error

        self._model_cache.mkdir(parents=True, exist_ok=True)
        try:
            model = WhisperModel(
                self._model_name,
                device="cpu",
                compute_type=self._compute_type,
                download_root=str(self._model_cache),
            )
            raw_segments, info = model.transcribe(
                str(media_path), language=language, vad_filter=vad, word_timestamps=word_timestamps
            )
            segments = tuple(
                TranscriptSegment(
                    start=float(segment.start),
                    end=float(segment.end),
                    text=segment.text.strip(),
                    words=tuple(
                        TranscriptWord(start=float(word.start), end=float(word.end), text=word.word.strip())
                        for word in (segment.words or [])
                        if word.start is not None and word.end is not None
                    ),
                )
                for segment in raw_segments
            )
        except Exception as error:
            raise RuntimeError(f"No se pudo transcribir '{media_path.name}': {error}") from error

        detected_language = language or getattr(info, "language", None)
        return TranscriptResult(model=self._model_name, language=detected_language, segments=segments)
