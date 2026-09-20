# LocalCallTranscriber v0.2.0 — Release notes

## Resumen

v0.2.0 añade una interfaz gráfica desktop opcional sin sustituir el CLI. CLI y
GUI usan la misma `TranscriptionApplication` y el mismo pipeline local de
faster-whisper.

## Novedades

- GUI PySide6/Qt Widgets opcional.
- Selección de un MP4 o carpeta y directorio de salida.
- Perfiles Rápido (`large-v3-turbo`) y Calidad (`large-v3`).
- Idioma automático, español o inglés.
- Hardware Automático, GPU o CPU.
- VAD, timestamps por palabra y overwrite configurables.
- Ejecución en background con `QThreadPool`.
- Progreso por archivos para lotes.
- Cancelación cooperativa después del archivo actual.
- Panel de diagnóstico y apertura del directorio de resultados.
- CLI nominal `local-call-transcriber` documentado para scripts y agentes de IA.

## CLI permanente

La GUI es opcional. Las dos invocaciones CLI siguen soportadas:

```powershell
.\.venv\Scripts\local-call-transcriber.exe .\llamada.mp4 --output-dir .\output
.\.venv\Scripts\python.exe -m local_call_transcriber .\llamada.mp4 --output-dir .\output
```

Consulta `docs/CLI_AGENT_USAGE.md` para el contrato completo orientado a
automatización y agentes.

## GUI desde el repositorio

```powershell
.\scripts\bootstrap.ps1 -WithGui
.\.venv\Scripts\python.exe -m local_call_transcriber.gui
```

También se instala `local-call-transcriber-gui.exe` dentro de
`.venv\Scripts`.

## Paquete Windows

La primera distribución GUI usa `pyside6-deploy`/Nuitka en modo
`standalone`. El artefacto se genera localmente con:

```powershell
.\scripts\package_gui.ps1
```

Los modelos Whisper no se incluyen en el paquete. El primer uso de un modelo
puede requerir conexión para descargarlo al cache local de LocalCallTranscriber.

## Privacidad

La transcripción continúa siendo local. Audio, vídeo y transcripciones no se
envían a una API cloud para completar el procesamiento.

## Compatibilidad

- Windows 11 nativo.
- Baseline validado: CPython 3.11.x.
- CPU obligatoria: `int8`.
- CUDA opcional.
- Sin WSL ni Docker.

## Notas de distribución

El paquete v0.2.0 inicial es standalone, no un instalador MSI y no un ejecutable
onefile. Esta forma se eligió para facilitar diagnóstico y validación de
dependencias nativas en la primera release GUI.

El tag `v0.2.0` sólo se crea después de completar
`docs/PHASE12_VALIDATION.md`.
