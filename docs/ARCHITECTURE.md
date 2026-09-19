# Arquitectura

## Principios

- Windows 11 nativo.
- Procesamiento local.
- CPU siempre funcional.
- GPU opcional y degradación limpia a CPU.
- Separar motor, configuración, entradas/salidas y automatización.
- Mantener `faster-whisper` detrás de una interfaz propia para evitar acoplamiento innecesario.

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
  config.py
  domain.py
  hardware.py
  orchestration.py
  outputs.py
  engines/
    base.py
    faster_whisper.py
```

La estructura exacta puede evolucionar si mejora la cohesión, pero deben conservarse las siguientes fronteras:

- `cli`: parsing y presentación, sin lógica pesada.
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

## Automatización

La primera interfaz operativa será una CLI para un archivo.

Después se añadirá procesamiento de carpeta.

Task Scheduler o un watcher persistente solo se evaluarán después de que el motor y el procesamiento por carpeta estén validados.

## Referencias técnicas

- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- CTranslate2: https://opennmt.net/CTranslate2/
- CUDA para Windows: https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/
- cuDNN para Windows: https://docs.nvidia.com/deeplearning/cudnn/installation/latest/windows.html
