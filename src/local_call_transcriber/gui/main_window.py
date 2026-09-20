"""Ventana Qt Widgets para configurar una operación de transcripción local."""

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from local_call_transcriber.application import (
    FileTranscriptionRun,
    FolderTranscriptionRun,
    TranscriptionApplication,
    TranscriptionRequest,
)

PROFILE_VALUES = {"Rápido": "large-v3-turbo", "Calidad": "large-v3"}
LANGUAGE_VALUES = {"Automático": None, "Español": "es", "Inglés": "en"}
HARDWARE_VALUES = {
    "Automático": ("auto", "auto"),
    "GPU": ("cuda", "float16"),
    "CPU": ("cpu", "int8"),
}


class MainWindow(QMainWindow):
    """Capa de presentación síncrona; background y progreso pertenecen a Fase 11."""

    def __init__(self, application: TranscriptionApplication | None = None) -> None:
        super().__init__()
        self._application = application or TranscriptionApplication()
        self.setWindowTitle("LocalCallTranscriber")
        self.setMinimumWidth(620)
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
        self.word_timestamps_checkbox = QCheckBox("Incluir timestamps por palabra en JSON")
        form.addRow("Timestamps:", self.word_timestamps_checkbox)
        self.overwrite_checkbox = QCheckBox("Sustituir salidas existentes")
        form.addRow("Overwrite:", self.overwrite_checkbox)
        layout.addLayout(form)

        self.transcribe_button = QPushButton("Transcribir")
        self.transcribe_button.clicked.connect(self.transcribe)
        layout.addWidget(self.transcribe_button)
        self.status_label = QLabel("Selecciona una entrada y un directorio de salida.")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        self.setCentralWidget(central)

    @staticmethod
    def _combo(values: dict[str, object]) -> QComboBox:
        combo = QComboBox()
        for label, value in values.items():
            combo.addItem(label, value)
        return combo

    def select_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Selecciona un MP4", filter="MP4 (*.mp4)")
        if path:
            self.input_path_edit.setText(path)

    def select_input_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Selecciona una carpeta con MP4")
        if path:
            self.input_path_edit.setText(path)

    def select_output_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Selecciona el directorio de salida")
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
        """Ejecuta la capa compartida directamente; no invoca el CLI ni subprocesses."""
        try:
            run = self._application.run(self.build_request())
        except (ValueError, RuntimeError) as error:
            self.status_label.setText(f"Error: {error}")
            return

        if isinstance(run, FileTranscriptionRun):
            self.status_label.setText(f"Completado. TXT: {run.outputs.txt}")
            return

        assert isinstance(run, FolderTranscriptionRun)
        successes = sum(item.status == "success" for item in run.results)
        failures = sum(item.status == "error" for item in run.results)
        skipped = sum(item.status == "skipped" for item in run.results)
        self.status_label.setText(
            f"Carpeta completada: {successes} éxito(s), {failures} error(es), {skipped} omitido(s)."
        )
