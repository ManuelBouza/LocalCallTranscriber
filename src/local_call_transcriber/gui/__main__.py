"""Punto de inicio opcional de la interfaz Qt Widgets."""

import sys


def main() -> int:
    """Crea la aplicación Qt sólo cuando el usuario solicita la GUI."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as error:
        raise SystemExit(
            "La GUI requiere PySide6. Ejecuta .\\scripts\\bootstrap.ps1 -WithGui. "
            "El CLI no necesita esta dependencia."
        ) from error

    from local_call_transcriber.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
