# LocalCallTranscriber

Aplicación local para Windows 11 orientada a la transcripción de archivos de llamadas, inicialmente MP4. Todo el procesamiento se realizará localmente.

## Estado

MVP `v0.1.0`: listo para Windows 11 nativo con PowerShell. El procesamiento es local; CPU funciona sin CUDA y GPU es opcional.

La primera integración prevista es `faster-whisper`. La estructura del proyecto permitirá incorporar otros motores posteriormente sin rehacer la aplicación.

La fase activa se mantiene en [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md).

## Requisitos de plataforma

- Windows 11 nativo
- PowerShell para automatización y scripts
- Python 3.11 o superior mediante `.venv`
- funcionamiento en CPU como ruta obligatoria
- CUDA opcional cuando el hardware y las dependencias sean compatibles
- sin WSL ni Docker

## Instalación desde un clone limpio

En PowerShell, instala CPython 3.11.x y Git. Clona el repositorio y prepara exclusivamente el entorno local `.venv`:

```powershell
git clone https://github.com/ManuelBouza/LocalCallTranscriber.git
Set-Location .\LocalCallTranscriber
.\scripts\bootstrap.ps1
.\scripts\test.ps1
```

El primer uso descarga el modelo seleccionado a `%LOCALAPPDATA%\LocalCallTranscriber\models`. No se descarga ni se sube audio, vídeo o transcripciones a ningún servicio.

## Documentación del proyecto

- [AGENTS.md](AGENTS.md): instrucciones permanentes para Codex.
- [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md): requisitos.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): arquitectura.
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md): fases y estado.
- [docs/ACCEPTANCE_CRITERIA.md](docs/ACCEPTANCE_CRITERIA.md): criterios de aceptación.
- [docs/DECISIONS.md](docs/DECISIONS.md): decisiones técnicas.
- [docs/CLI_AGENT_USAGE.md](docs/CLI_AGENT_USAGE.md): contrato práctico del CLI para scripts y agentes de IA.

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

El comando genera `llamada.txt`, `llamada.json`, `llamada.srt` y `llamada.vtt`. El JSON incluye al menos el modelo, idioma, segmentos y sus timestamps. Omite `--language` para detectar el idioma automáticamente o indica, por ejemplo, `--language es`.

Usa `--word-timestamps` para incluir timestamps por palabra en el JSON. Las salidas se ordenan cronológicamente. Por seguridad, el CLI rechaza salidas existentes; añade `--overwrite` solo cuando quieras sustituir explícitamente los cuatro archivos de esa llamada.

El primer uso de un modelo lo descarga a `%LOCALAPPDATA%\LocalCallTranscriber\models`; no se versiona. Para validar la ruta real CPU con un MP4 temporal generado por PyAV:

```powershell
.\scripts\smoke_cpu.ps1
```

## CUDA opcional

La CLI admite `--device auto`, `--device cuda` y `--device cpu`. `auto` intenta GPU y vuelve a CPU `int8` si CUDA no se inicializa; `cuda` falla con un diagnóstico accionable para no ocultar una instalación incompleta.

La combinación validada en este equipo es CUDA Toolkit 12.6, cuDNN 9.11.0.98 para CUDA 12, faster-whisper 1.2.1 y CTranslate2 4.8.2. Se verificó mediante transcripciones locales reales en `float16` e `int8_float16`.

```powershell
.\.venv\Scripts\python.exe -m local_call_transcriber .\llamada.mp4 --device auto --compute-type auto
```

## Benchmark reproducible

La Fase 5 añade un benchmark local que genera voz mediante el sintetizador de Windows, la convierte temporalmente a MP4 y mide la misma CLI de producción. El JSON queda fuera de Git en `%LOCALAPPDATA%\LocalCallTranscriber\benchmarks`:

```powershell
.\scripts\benchmark.ps1
```

Compara `large-v3` y `large-v3-turbo` en CPU `int8` y GPU `float16`/`int8_float16`. Registra duración, tiempo total, RTF, segmentos y una comparación cualitativa con la referencia local. Para incluir MP4 locales propios sin copiarlos ni versionarlos:

```powershell
.\scripts\benchmark.ps1 -InputMp4 'D:\Llamadas\muestra-controlada.mp4'
```

## Procesamiento por carpeta

Pasa un directorio que contenga MP4 (sin recorrer subdirectorios). Cada archivo continúa de forma independiente aunque otro falle. Los resultados se escriben en `--output-dir`, se registra una línea JSON por archivo en `folder-run.jsonl` y se muestra un resumen final.

```powershell
.\.venv\Scripts\python.exe -m local_call_transcriber .\input --output-dir .\output
```

Por seguridad, un MP4 con cualquiera de sus salidas existentes queda omitido. Usa `--overwrite` sólo para volver a procesar deliberadamente esos archivos.

## Automatización diaria

Se eligió Windows Task Scheduler, no un watcher persistente: no deja un proceso residente y reutiliza la misma CLI de carpeta. Crea una tarea diaria (por defecto, 02:00):

```powershell
.\scripts\register_folder_task.ps1 -InputDirectory 'D:\Llamadas\input' -OutputDirectory 'D:\Llamadas\output' -Time '02:00'
```

Prueba el pipeline sin programarlo ejecutando el runner directamente. `automation.log` y `folder-run.jsonl` quedan en la salida:

```powershell
.\scripts\run_folder_task.ps1 -InputDirectory 'D:\Llamadas\input' -OutputDirectory 'D:\Llamadas\output'
```

Para deshabilitarla, elimina la tarea:

```powershell
.\scripts\unregister_folder_task.ps1
```

## Troubleshooting

- **No se encontró CPython 3.11:** instala Python con `py install 3.11` y ejecuta de nuevo `bootstrap.ps1`.
- **CUDA no es utilizable:** ejecuta `./scripts/doctor.ps1`. La aplicación sigue siendo usable con `--device cpu --compute-type int8`.
- **El modelo tarda o falla al descargarse:** verifica red y espacio libre; el modelo se guarda localmente fuera del repositorio.
- **Una llamada se omite al procesar carpeta:** ya existen salidas. Revisa `folder-run.jsonl`; usa `--overwrite` sólo si quieres sustituirlas.
- **La tarea diaria no se ejecuta:** prueba primero `run_folder_task.ps1` manualmente y revisa `automation.log` en el directorio de salida.


## Interfaz CLI y futura GUI

El CLI es una interfaz permanente del proyecto y seguirá disponible aunque exista una GUI. Para automatización o uso desde agentes de IA consulta [docs/CLI_AGENT_USAGE.md](docs/CLI_AGENT_USAGE.md).

La GUI planificada para v0.2.0 será una capa opcional PySide6/Qt Widgets sobre la misma lógica de aplicación; no sustituirá el CLI.
