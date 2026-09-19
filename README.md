# LocalCallTranscriber

Aplicación local para Windows 11 orientada a la transcripción de archivos de llamadas, inicialmente MP4. Todo el procesamiento se realizará localmente.

## Estado

El proyecto está en fase de especificación e implementación incremental.

La primera integración prevista es `faster-whisper`. La estructura del proyecto permitirá incorporar otros motores posteriormente sin rehacer la aplicación.

La fase activa se mantiene en [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md).

## Requisitos de plataforma

- Windows 11 nativo
- PowerShell para automatización y scripts
- Python 3.11 o superior mediante `.venv`
- funcionamiento en CPU como ruta obligatoria
- CUDA opcional cuando el hardware y las dependencias sean compatibles
- sin WSL ni Docker

## Documentación del proyecto

- [AGENTS.md](AGENTS.md): instrucciones permanentes para Codex.
- [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md): requisitos.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): arquitectura.
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md): fases y estado.
- [docs/ACCEPTANCE_CRITERIA.md](docs/ACCEPTANCE_CRITERIA.md): criterios de aceptación.
- [docs/DECISIONS.md](docs/DECISIONS.md): decisiones técnicas.

El repositorio es la fuente de verdad para la implementación. Los prompts dirigidos a Codex deben poder mantenerse mínimos leyendo estas especificaciones.

## Estructura

```text
src/local_call_transcriber/
  engines/     # Adaptadores de motores de transcripción
tests/         # Pruebas automatizadas
scripts/       # Automatización en PowerShell
docs/          # Especificaciones versionadas
```

No se versionan modelos, archivos multimedia, entornos virtuales ni resultados de transcripción.

## Preflight del equipo

La fase inicial incluye un diagnóstico de solo lectura. No instala paquetes, no modifica `PATH` y no requiere privilegios administrativos para sus comprobaciones habituales.

Ejecuta desde PowerShell, en la raíz del repositorio:

```powershell
.\scripts\doctor.ps1
```

Para una salida estructurada destinada a automatización o validación:

```powershell
.\scripts\doctor.ps1 -AsJson
```

La salida informa Windows, PowerShell, todos los intérpretes Python detectables, GPU NVIDIA/driver/VRAM cuando `nvidia-smi` está disponible, CUDA Toolkit, runtime CUDA, cuBLAS, cuDNN, CTranslate2 y espacio libre. Para CTranslate2 indica el intérprete y la versión detectados. Las bibliotecas CUDA se buscan de forma no destructiva en el `PATH` efectivo y en ubicaciones NVIDIA conocidas. Cada comprobación usa `PASS`, `WARN`, `FAIL` o `NOT_FOUND`.

La validación automatizada de la estructura del informe se ejecuta con:

```powershell
.\tests\test_doctor.ps1
```

## Bootstrap de desarrollo

La ruta normal de bootstrap crea o reutiliza `.venv` con **CPython 3.11.x**, el baseline validado para el MVP. Usa el launcher de Python para Windows (`py`) y no selecciona el primer `python.exe` de `PATH`. Todas las herramientas de desarrollo se instalan únicamente dentro de ese entorno; no se modifica Python global, `PATH`, CUDA ni cuDNN.

Si CPython 3.11 no está disponible, instala esa versión y vuelve a ejecutar el bootstrap:

```powershell
py install 3.11
```

```powershell
.\scripts\bootstrap.ps1
```

Para un experimento controlado puede usarse un intérprete concreto compatible (3.12 o posterior). El bootstrap puede crear e instalar el paquete en ese entorno, pero lo marca como no validado; `scripts/test.ps1` no permitirá utilizarlo como ruta normal:

```powershell
.\scripts\bootstrap.ps1 -PythonExecutable 'C:\Ruta\A\python.exe'
```

Ejecuta la suite completa —pruebas, lint, smoke test y la validación del preflight— con:

```powershell
.\scripts\test.ps1
```

`requirements-dev.txt` es el lock local: fija las dependencias directas y transitivas de las pruebas, lint, build y runtime CPU. Sus actualizaciones deben ser deliberadas y validarse con `./scripts/test.ps1`. La combinación CUDA/cuDNN permanece fuera de este lock hasta su fase de validación específica.

## Transcripción CPU inicial

La primera ruta operativa usa `faster-whisper 1.2.1` con `device=cpu` y `compute_type=int8`. PyAV, incluido por la dependencia, decodifica MP4 sin una instalación externa de FFmpeg.

```powershell
.\.venv\Scripts\python.exe -m local_call_transcriber .\llamada.mp4 --output-dir .\output --model tiny --device cpu --compute-type int8
```

El comando genera `llamada.txt` y `llamada.json`. El JSON incluye al menos el modelo, idioma, segmentos y sus timestamps. Omite `--language` para detectar el idioma automáticamente o indica, por ejemplo, `--language es`.

El primer uso de un modelo lo descarga a `%LOCALAPPDATA%\LocalCallTranscriber\models`; no se versiona. Para validar la ruta real CPU con un MP4 temporal generado por PyAV:

```powershell
.\scripts\smoke_cpu.ps1
```
