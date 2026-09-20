"""Workers Qt para ejecutar transcripciones fuera del hilo de eventos."""

from threading import Event

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from local_call_transcriber.application import (
    TranscriptionApplication,
    TranscriptionRequest,
    TranscriptionRun,
)
from local_call_transcriber.orchestration import FolderItemResult


class WorkerSignals(QObject):
    """Señales thread-safe consumidas por la ventana principal."""

    item_started = Signal(str, int, int)
    item_finished = Signal(object, int, int)
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()


class TranscriptionWorker(QRunnable):
    """Ejecuta una solicitud y permite cancelarla entre archivos."""

    def __init__(
        self,
        application: TranscriptionApplication,
        request: TranscriptionRequest,
    ) -> None:
        super().__init__()
        self._application = application
        self._request = request
        self._cancel_requested = Event()
        self.signals = WorkerSignals()

    def request_cancel(self) -> None:
        """Solicita detener el lote después del archivo actualmente en proceso."""
        self._cancel_requested.set()

    def is_cancel_requested(self) -> bool:
        return self._cancel_requested.is_set()

    def _item_started(self, path: object, index: int, total: int) -> None:
        self.signals.item_started.emit(str(path), index, total)

    def _item_finished(
        self,
        item: FolderItemResult,
        index: int,
        total: int,
    ) -> None:
        self.signals.item_finished.emit(item, index, total)

    @Slot()
    def run(self) -> None:
        try:
            result: TranscriptionRun = self._application.run(
                self._request,
                on_item_started=self._item_started,
                on_item_finished=self._item_finished,
                should_cancel=self.is_cancel_requested,
            )
        except (ValueError, RuntimeError) as error:
            self.signals.failed.emit(str(error))
        except Exception as error:  # pragma: no cover - protección final del worker Qt
            self.signals.failed.emit(f"Error inesperado: {error}")
        else:
            self.signals.completed.emit(result)
        finally:
            self.signals.finished.emit()
