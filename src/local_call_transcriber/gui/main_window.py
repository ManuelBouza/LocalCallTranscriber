"""Ventana Qt Widgets para configurar y operar transcripciones locales."""

from pathlib import Path

from PySide6.QtCore import QThreadPool, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from local_call_transcriber.application import (
    FileTranscriptionRun,
    FolderTranscriptionRun,
    TranscriptionApplication,
    TranscriptionRequest,
    TranscriptionRun,
)
from local_call_transcriber.gui.workers import TranscriptionWorker
from local_call_transcriber.orchestration import FolderItemResult

PROFILE_VALUES = {"Rápido": "large-v3-turbo", "Calidad": "large-v3"}
LANGUAGE_VALUES = {"Automático": None, "Español": "es", "Inglés": "en"}
HARDWARE_VALUES = {
    "Automático": ("auto", "auto"),
    "GPU": ("cuda", "float16"),
    "CPU": ("cpu", "int8"),
}


class MainWindow(QMainWindow):
    """Capa de presentación Qt; los trabajos pesados se ejecutan en QThreadPool."""

    def __init__(self, application: TranscriptionApplication | None = None) -> None:
        super().__init__()
        self._application = application or TranscriptionApplication()
        self._thread_pool = QThreadPool(self)
        self._worker: TranscriptionWorker | None = None
        self._cancel_requested = False
        self.setWindowTitle("LocalCallTranscriber")
        self.setMinimumWidth(700)
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget(self)
        layout = QVBoxLayout(central)
        form = QFormLayout()

        self.input_path_edit = QLineEdit()
        input_buttons = QHBoxLayout()
        input_buttons.addWidget(self.input_path_edit)
        file_button = QPushButton("Seleccionar MP4…")
        file_button.clicked.connect(self.select_file)
        input_buttons.addWidget(file_button)
        folder_button = QPushButton("Seleccionar carpeta…")
        folder_button.clicked.connect(self.select_input_folder)
        input_buttons.addWidget(folder_button)
        form.addRow("Archivo o carpeta:", input_buttons)

        self.output_dir_edit = QLineEdit()
        output_buttons = QHBoxLayout()
        output_buttons.addWidget(self.output_dir_edit)
        output_button = QPushButton("Seleccionar salida…")
        output_button.clicked.connect(self.select_output_folder)
        output_buttons.addWidget(output_button)
        form.addRow("Directorio de salida:", output_buttons)

        self.profile_combo = self._combo(PROFILE_VALUES)
        form.addRow("Perfil:", self.profile_combo)
        self.language_combo = self._combo(LANGUAGE_VALUES)
        form.addRow("Idioma:", self.language_combo)
        self.hardware_combo = self._combo(HARDWARE_VALUES)
        form.addRow("Hardware:", self.hardware_combo)

        self.vad_checkbox = QCheckBox("Usar filtro de actividad de voz (VAD)")
        self.vad_checkbox.setChecked(True)
        form.addRow("VAD:", self.vad_checkbox)
        self.word_timestamps_checkbox = QCheckBox(
            "Incluir timestamps por palabra en JSON"
        )
        form.addRow("Timestamps:", self.word_timestamps_checkbox)
        self.overwrite_checkbox = QCheckBox("Sustituir salidas existentes")
        form.addRow("Overwrite:", self.overwrite_checkbox)
        layout.addLayout(form)

        actions = QHBoxLayout()
        self.transcribe_button = QPushButton("Transcribir")
        self.transcribe_button.clicked.connect(self.transcribe)
        actions.addWidget(self.transcribe_button)

        self.cancel_button = QPushButton("Cancelar después del actual")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_current_run)
        actions.addWidget(self.cancel_button)

        self.open_output_button = QPushButton("Abrir resultados")
        self.open_output_button.clicked.connect(self.open_results)
        actions.addWidget(self.open_output_button)
        layout.addLayout(actions)

        self.current_file_label = QLabel("Sin trabajo activo.")
        self.current_file_label.setWordWrap(True)
        layout.addWidget(self.current_file_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel(
            "Selecciona una entrada y un directorio de salida."
        )
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("Diagnóstico de la ejecución")
        layout.addWidget(self.log_view)

        self.setCentralWidget(central)

    @staticmethod
    def _combo(values: dict[str, object]) -> QComboBox:
        combo = QComboBox()
        for label, value in values.items():
            combo.addItem(label, value)
        return combo

    def select_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecciona un MP4",
            filter="MP4 (*.mp4)",
        )
        if path:
            self.input_path_edit.setText(path)

    def select_input_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "Selecciona una carpeta con MP4",
        )
        if path:
            self.input_path_edit.setText(path)

    def select_output_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "Selecciona el directorio de salida",
        )
        if path:
            self.output_dir_edit.setText(path)

    def build_request(self) -> TranscriptionRequest:
        """Traduce los controles visibles a la misma solicitud que usa el CLI."""
        input_text = self.input_path_edit.text().strip()
        output_text = self.output_dir_edit.text().strip()
        if not input_text:
            raise ValueError("Selecciona un archivo MP4 o una carpeta de entrada.")
        if not output_text:
            raise ValueError("Selecciona un directorio de salida.")
        device, compute_type = self.hardware_combo.currentData()
        return TranscriptionRequest(
            input_path=Path(input_text),
            output_dir=Path(output_text),
            model=self.profile_combo.currentData(),
            language=self.language_combo.currentData(),
            device=device,
            compute_type=compute_type,
            vad=self.vad_checkbox.isChecked(),
            word_timestamps=self.word_timestamps_checkbox.isChecked(),
            overwrite=self.overwrite_checkbox.isChecked(),
        )

    def transcribe(self) -> None:
        """Inicia la transcripción fuera del hilo de eventos Qt."""
        if self._worker is not None:
            return

        try:
            request = self.build_request()
        except ValueError as error:
            self.status_label.setText(f"Error: {error}")
            return

        self.log_view.clear()
        self._cancel_requested = False
        self.transcribe_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.status_label.setText("Preparando transcripción…")
        self.current_file_label.setText("Esperando inicio del primer archivo…")
        self.progress_bar.setRange(0, 0)
        self._append_log(f"INICIO — {request.input_path}")

        worker = TranscriptionWorker(self._application, request)
        worker.signals.item_started.connect(self._on_item_started)
        worker.signals.item_finished.connect(self._on_item_finished)
        worker.signals.completed.connect(self._on_completed)
        worker.signals.failed.connect(self._on_failed)
        worker.signals.finished.connect(self._on_finished)
        self._worker = worker
        self._thread_pool.start(worker)

    def cancel_current_run(self) -> None:
        """Solicita detener un lote cuando termine el archivo en proceso."""
        if self._worker is None:
            return
        self._cancel_requested = True
        self._worker.request_cancel()
        self.cancel_button.setEnabled(False)
        self.status_label.setText(
            "Cancelación solicitada. El archivo actual terminará de forma segura."
        )
        self._append_log("CANCELACIÓN SOLICITADA — no se iniciarán más archivos.")

    def open_results(self) -> None:
        """Abre el directorio de salida con el shell de Windows."""
        output_text = self.output_dir_edit.text().strip()
        if not output_text:
            self.status_label.setText("Error: selecciona un directorio de salida.")
            return
        output_dir = Path(output_text)
        if not output_dir.is_dir():
            self.status_label.setText(
                f"Error: el directorio de salida todavía no existe: {output_dir}"
            )
            return
        opened = QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(output_dir.resolve()))
        )
        if not opened:
            self.status_label.setText(
                f"No se pudo abrir el directorio de salida: {output_dir}"
            )

    def _on_item_started(self, source: str, index: int, total: int) -> None:
        name = Path(source).name
        self.current_file_label.setText(f"Procesando: {name} ({index}/{total})")
        self.status_label.setText(f"Procesando {name}…")
        self._append_log(f"PROCESANDO {index}/{total} — {source}")

        if total <= 1:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(index - 1)

    def _on_item_finished(
        self,
        item: object,
        index: int,
        total: int,
    ) -> None:
        if not isinstance(item, FolderItemResult):
            return
        self._append_log(
            f"{item.status.upper()} {index}/{total} — "
            f"{item.source.name} — {item.detail}"
        )
        if total > 1:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(index)

    def _on_completed(self, run: object) -> None:
        if isinstance(run, FileTranscriptionRun):
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
            self.current_file_label.setText("Archivo finalizado.")
            if self._cancel_requested:
                self.status_label.setText(
                    "Archivo completado. La cancelación no interrumpe un MP4 en curso."
                )
            else:
                self.status_label.setText(f"Completado. TXT: {run.outputs.txt}")
            self._append_log(f"COMPLETADO — TXT: {run.outputs.txt}")
            return

        if not isinstance(run, FolderTranscriptionRun):
            return

        successes = sum(item.status == "success" for item in run.results)
        failures = sum(item.status == "error" for item in run.results)
        skipped = sum(item.status == "skipped" for item in run.results)
        processed = len(run.results)

        if run.total:
            self.progress_bar.setRange(0, run.total)
            self.progress_bar.setValue(processed)
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)

        summary = (
            f"{successes} éxito(s), {failures} error(es), "
            f"{skipped} omitido(s)"
        )
        if run.cancelled:
            self.current_file_label.setText("Lote detenido de forma segura.")
            self.status_label.setText(
                f"Cancelado después del archivo actual: {processed}/{run.total}. "
                f"{summary}."
            )
            self._append_log(
                f"CANCELADO — procesados {processed}/{run.total}; {summary}."
            )
        else:
            self.current_file_label.setText("Carpeta finalizada.")
            self.status_label.setText(f"Carpeta completada: {summary}.")
            self._append_log(f"COMPLETADO — {summary}.")

    def _on_failed(self, message: str) -> None:
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.current_file_label.setText("La ejecución terminó con error.")
        self.status_label.setText(f"Error: {message}")
        self._append_log(f"ERROR — {message}")

    def _on_finished(self) -> None:
        self.transcribe_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self._worker = None

    def _append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    @property
    def is_running(self) -> bool:
        """Permite a pruebas y diagnósticos consultar el estado sin tocar el worker."""
        return self._worker is not None
