"""Adaptador de faster-whisper con CPU obligatoria y CUDA opcional."""

from pathlib import Path

from local_call_transcriber.domain import TranscriptResult, TranscriptSegment, TranscriptWord
from local_call_transcriber.hardware import prepare_cuda_runtime


class FasterWhisperEngine:
    def __init__(
        self, model_name: str, model_cache: Path, device: str = "auto", compute_type: str = "auto"
    ) -> None:
        self._model_name = model_name
        self._model_cache = model_cache
        self._device = device
        self._compute_type = compute_type

    def _create_model(self, whisper_model: object, device: str, compute_type: str) -> object:
        if device == "cuda":
            prepare_cuda_runtime()
        return whisper_model(
            self._model_name,
            device=device,
            compute_type=compute_type,
            download_root=str(self._model_cache),
        )

    def _load_model(self, whisper_model: object) -> object:
        if self._device == "cpu":
            compute_type = "int8" if self._compute_type == "auto" else self._compute_type
            if compute_type != "int8":
                raise RuntimeError("En CPU sólo está validado compute_type=int8.")
            return self._create_model(whisper_model, "cpu", compute_type)

        cuda_compute_type = "float16" if self._compute_type == "auto" else self._compute_type
        if self._device == "cuda":
            try:
                return self._create_model(whisper_model, "cuda", cuda_compute_type)
            except Exception as error:
                raise RuntimeError(
                    "CUDA no es utilizable para faster-whisper. Ejecuta .\\scripts\\doctor.ps1 "
                    "y verifica CUDA 12, cuBLAS y cuDNN 9. "
                    f"Detalle: {error}"
                ) from error

        try:
            return self._create_model(whisper_model, "cuda", cuda_compute_type)
        except Exception as error:
            print(f"Aviso: CUDA no se pudo inicializar ({error}). Se usará CPU con int8.")
            return self._create_model(whisper_model, "cpu", "int8")

    def transcribe(
        self, media_path: Path, language: str | None, vad: bool, word_timestamps: bool
    ) -> TranscriptResult:
        if self._device in {"auto", "cuda"}:
            prepare_cuda_runtime()
        try:
            from faster_whisper import WhisperModel
        except ImportError as error:
            raise RuntimeError(
                "faster-whisper no está instalado en .venv. Ejecuta .\\scripts\\bootstrap.ps1."
            ) from error

        self._model_cache.mkdir(parents=True, exist_ok=True)
        try:
            model = self._load_model(WhisperModel)
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
