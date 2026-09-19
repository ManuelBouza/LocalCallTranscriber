"""Modelos de datos independientes del motor de transcripción."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    end: float
    text: str
    words: tuple["TranscriptWord", ...] = ()


@dataclass(frozen=True)
class TranscriptWord:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class TranscriptResult:
    model: str
    language: str | None
    segments: tuple[TranscriptSegment, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "language": self.language,
            "segments": [asdict(segment) for segment in sorted(self.segments, key=lambda segment: segment.start)],
        }
