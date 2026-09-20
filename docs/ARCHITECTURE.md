# Arquitectura

## Principios

- Windows 11 nativo.
- Procesamiento local.
- CPU siempre funcional.
- GPU opcional y degradación limpia a CPU.
- Separar motor, configuración, entradas/salidas y automatización.
- Mantener `faster-whisper` detrás de una interfaz propia para evitar acoplamiento innecesario.
- Mantener el CLI como interfaz permanente, estable y automatizable.
- Tratar la GUI como una capa opcional de presentación, nunca como reemplazo del CLI.

## Interfaces de usuario y automatización

La arquitectura post-MVP debe conservar una sola lógica de aplicación compartida:

```text
CLI ─────┐
         ├──> Application/service layer ──> orchestration ──> engine ──> outputs
GUI ─────┘
```

Reglas:

- el CLI continúa siendo una interfaz de primer nivel;
- la GUI no implementa un segundo pipeline;
- la GUI no debe lanzar el CLI como subprocess para ejecutar una transcripción normal;
- CLI y GUI construyen las mismas solicitudes/configuraciones y llaman a la misma capa de aplicación;
- las dependencias exclusivas de GUI no deben ser necesarias para ejecutar el CLI;
- `docs/CLI_AGENT_USAGE.md` define el uso del CLI como herramienta para agentes de IA.

La GUI seleccionada para v0.2.0 es **PySide6 + Qt Widgets**. Los trabajos largos se ejecutarán fuera del hilo de eventos de Qt mediante workers/`QThreadPool` o un mecanismo equivalente de Qt.

## Flujo principal

```text
MP4 local
   |
   v
decoder de PyAV
   |
   v
VAD / preparación
   |
   v
Engine interface
   |
   +--> FasterWhisperEngine
   |
   v
TranscriptResult
   |
   +--> TXT
   +--> JSON
   +--> SRT
   +--> VTT
```

`faster-whisper` utiliza PyAV para decodificación, por lo que el flujo principal no debe exigir una instalación externa de FFmpeg salvo que una futura función lo necesite y se documente.

## Módulos previstos

```text
src/local_call_transcriber/
  cli.py
  application.py
  config.py
  domain.py
  hardware.py
  orchestration.py
  outputs.py
  engines/
    base.py
    faster_whisper.py
  gui/
    __init__.py
    __main__.py
    main_window.py
    workers.py
```

La estructura exacta puede evolucionar si mejora la cohesión, pero deben conservarse las siguientes fronteras:

- `cli`: parsing y presentación CLI, sin lógica pesada; contrato permanente para humanos/scripts/agentes.
- `application`: `TranscriptionRequest`, construcción de engine y servicio compartido por CLI y GUI. No depende de argumentos CLI ni de Qt.
- `gui`: presentación Qt Widgets; traduce controles a `TranscriptionRequest` y llama a `TranscriptionApplication`. No contiene lógica de transcripción duplicada ni invoca el CLI. Los workers se incorporarán en Fase 11.
- `config`: lectura/validación TOML y defaults.
- `domain`: modelos de datos independientes del motor.
- `hardware`: detección de CPU/CUDA y compute types.
- `engines`: adaptadores de motores de transcripción.
- `outputs`: serialización TXT/JSON/SRT/VTT.
- `orchestration`: coordinación del flujo sin depender de detalles de CLI.

## Configuración

Formato: TOML.

Configuraciones previstas:

```toml
[transcription]
model = "large-v3-turbo"
language = "auto"
vad = true
word_timestamps = false

[hardware]
device = "auto"
compute_type = "auto"

[output]
txt = true
json = true
srt = true
vtt = true
```

Los valores finales por defecto se fijarán después del benchmark de hardware.

## Modelos

Perfiles iniciales:

- `quality`: `large-v3`;
- `fast`: `large-v3-turbo`.

No almacenar modelos en Git.

El directorio de cache debe ser configurable. La implementación deberá usar una ubicación local apropiada para Windows y documentarla.

## Hardware

Modos soportados:

- `cpu`;
- `cuda`;
- `auto`.

### CPU

Baseline inicial:
- `compute_type=int8`.

### CUDA

Se deberán detectar y validar realmente:
- GPU NVIDIA;
- driver;
- runtime disponible para CTranslate2;
- compute types soportados.

No se considerará CUDA funcional únicamente porque `nvidia-smi` responda.

Los perfiles candidatos iniciales son:
- `float16`;
- `int8_float16`.

### Auto

`auto` intentará seleccionar la mejor ruta validada. Si la inicialización CUDA falla, deberá poder continuar en CPU y registrar claramente el fallback.

## Dependencias

PySide6 6.8.3 es un extra opcional (`.[gui]`) y también está fijado en
`requirements-gui.txt`. El runtime core y el CLI no lo declaran como dependencia
obligatoria; `scripts/bootstrap.ps1 -WithGui` lo instala sólo en `.venv`.

Versión candidata inicial investigada:
- `faster-whisper 1.2.1`.

Baseline CPU validado localmente para la Fase 2:
- CPython `3.11.9`;
- `faster-whisper 1.2.1`;
- `CTranslate2 4.8.2`;
- `PyAV 18.1.0`;
- `device=cpu`, `compute_type=int8`.

Esta combinación valida únicamente CPU. No implica compatibilidad CUDA/cuDNN, que queda para su fase específica.

No debe fijarse definitivamente una combinación `faster-whisper/CTranslate2/CUDA/cuDNN` hasta completar las fases de preflight y validación local.

La instalación GPU actual de faster-whisper requiere prestar especial atención a la compatibilidad entre CTranslate2, CUDA 12, cuBLAS y cuDNN 9. El proyecto no debe instalar ciegamente "latest" sin validar la combinación.

Combinación CUDA validada localmente en Fase 4: NVIDIA GeForce RTX 2060 (driver 591.74), CUDA Toolkit 12.6, cuBLAS de CUDA 12.6, cuDNN 9.11.0.98 para CUDA 12, CPython 3.11.9, faster-whisper 1.2.1 y CTranslate2 4.8.2. Las DLL de CUDA/cuDNN se preparan sólo para el proceso antes de cargar CTranslate2; CPU sigue disponible sin ellas.

## Automatización

La primera interfaz operativa será una CLI para un archivo.

Después se añadirá procesamiento de carpeta.

Task Scheduler o un watcher persistente solo se evaluarán después de que el motor y el procesamiento por carpeta estén validados.

## Referencias técnicas

- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- CTranslate2: https://opennmt.net/CTranslate2/
- CUDA para Windows: https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/
- cuDNN para Windows: https://docs.nvidia.com/deeplearning/cudnn/installation/latest/windows.html
