# Changelog

## v0.2.0 — GUI desktop

- GUI opcional PySide6/Qt Widgets sobre la misma `TranscriptionApplication` del CLI.
- Selección de archivo/carpeta, salida, perfiles Rápido/Calidad, idioma, hardware, VAD, word timestamps y overwrite.
- Ejecución en background mediante `QThreadPool`, con ventana responsiva.
- Progreso real por archivos para carpetas y estado indeterminado para un MP4 individual.
- Cancelación cooperativa después del archivo actual, preservando outputs y `folder-run.jsonl`.
- Panel de diagnóstico y apertura del directorio de resultados.
- CLI permanente para humanos, scripts y agentes de IA, con entry point `local-call-transcriber`.
- Empaquetado Windows reproducible preparado mediante `pyside6-deploy`/Nuitka en modo standalone.
- Smoke no interactivo del paquete con MP4 temporal, modelo `tiny`, CPU `int8` y validación TXT/JSON/SRT/VTT.
- Modelos y datos de llamadas siguen fuera del repositorio y del artefacto de release.

## v0.1.0 — MVP

- Transcripción local de MP4 con faster-whisper, en CPU y CUDA opcional.
- Salidas TXT, JSON, SRT y VTT, con timestamps por palabra opcionales.
- Procesamiento seguro de carpetas y automatización diaria mediante Windows Task Scheduler.
- Benchmark reproducible de la ruta CLI y diagnóstico PowerShell del entorno.
- Sin WSL, Docker, servicios cloud, modelos ni datos de llamadas versionados.
