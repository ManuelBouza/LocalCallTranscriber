# Plan de implementación

Este documento define el orden obligatorio de trabajo. La implementación inicial de la fase `NEXT` corresponde normalmente a ChatGPT; Codex verifica y corrige esa implementación en el equipo local conforme a `AGENTS.md`. Ningún participante debe avanzar a una fase posterior sin la transición explícita del plan.

Estados permitidos:
- `DONE`
- `NEXT`
- `BLOCKED`
- `PENDING`

## Fase 0 — Preflight del equipo

**Estado: DONE**

Objetivo: conocer el estado real del equipo sin modificarlo.

Entregables previstos:
- `scripts/doctor.ps1`;
- informe legible del entorno;
- detección de Windows, PowerShell y Python;
- detección de GPU NVIDIA, driver y VRAM cuando exista;
- detección no destructiva de CUDA/cuDNN/CTranslate2 si ya están presentes;
- comprobación de espacio libre relevante;
- recomendaciones basadas en hechos detectados.

Restricción: esta fase no instalará faster-whisper, CUDA, cuDNN ni modificará PATH global.

Completado: `scripts/doctor.ps1` produce un informe de solo lectura, legible o JSON, y `tests/test_doctor.ps1` valida automáticamente su estructura y estados. La detección cubre todos los intérpretes Python encontrados, CTranslate2 por intérprete y toolkit/runtimes CUDA, cuBLAS y cuDNN en el entorno efectivo.

## Fase 1 — Bootstrap reproducible de desarrollo

**Estado: DONE**

Objetivo: crear el entorno Python local y el conjunto mínimo de herramientas del proyecto.

Entregables previstos:
- bootstrap PowerShell;
- creación/reutilización segura de `.venv`;
- instalación reproducible de dependencias de desarrollo;
- pytest y linting;
- smoke test del paquete;
- estrategia de bloqueo/pinning documentada.

No incluirá todavía cambios globales de CUDA/cuDNN.

Completado: la ruta normal permanece fijada a CPython 3.11.x. La metadata acepta Python 3.11+ para que `-PythonExecutable` pueda instalar entornos experimentales de minors posteriores, que quedan advertidos como no soportados y no pueden ejecutar la ruta normal de `scripts/test.ps1`.

## Fase 2 — Transcripción CPU baseline

**Estado: DONE**

Objetivo: transcribir un MP4 completamente en CPU.

Entregables previstos:
- interfaz de engine;
- adaptador `faster-whisper`;
- CLI mínima;
- `device=cpu`;
- `compute_type=int8`;
- idioma auto/explícito;
- VAD;
- TXT y JSON;
- pruebas unitarias;
- smoke test real con fixture permitido localmente.

Completado: CLI CPU basada en `faster-whisper 1.2.1`, con `device=cpu`, `compute_type=int8`, VAD e idioma auto/explícito. Produce TXT y JSON, valida entradas y cuenta con pruebas unitarias y smoke test local de MP4 generado con PyAV.

## Fase 3 — Formatos y timestamps

**Estado: DONE**

Objetivo: completar las salidas de usuario.

Entregables previstos:
- SRT;
- VTT;
- timestamps por segmento;
- timestamps por palabra configurables;
- validación de nombres/rutas de salida;
- pruebas de serialización.

Completado: serializadores TXT, JSON, SRT y VTT con segmentos ordenados cronológicamente. `--word-timestamps` habilita las palabras en JSON y `--overwrite` exige una decisión explícita antes de reemplazar salidas existentes. Las pruebas cubren formatos, orden, timestamps y la protección contra sobrescritura.

## Fase 4 — Aceleración CUDA opcional

**Estado: DONE**

Objetivo: habilitar GPU sin romper CPU.

Entregables previstos:
- validación real de CTranslate2 sobre CUDA;
- diagnóstico accionable de incompatibilidades;
- `device=auto|cuda|cpu`;
- fallback `cuda -> cpu` en modo auto;
- pruebas de `float16` e `int8_float16`;
- documentación exacta de la combinación validada de driver/runtime/librerías.

Las instalaciones de CUDA/cuDNN que sean necesarias deberán estar justificadas por el preflight y ser explícitas.

Completado: la CLI admite `--device cpu|cuda|auto`. `auto` intenta CUDA y vuelve a CPU `int8` con aviso si falla la inicialización; `cuda` informa un diagnóstico accionable. Se validaron transcripciones reales con CTranslate2 sobre la RTX 2060 en `float16` e `int8_float16`.

## Fase 5 — Benchmark y defaults

**Estado: DONE**

Objetivo: escoger defaults por evidencia sobre el equipo real.

Comparaciones mínimas:
- `large-v3` frente a `large-v3-turbo`;
- CPU `int8`;
- GPU `float16`;
- GPU `int8_float16`;
- batch sizes viables cuando proceda.

Métricas:
- duración del archivo;
- tiempo total;
- real-time factor;
- RAM;
- VRAM cuando sea posible;
- observaciones de calidad sobre un conjunto de prueba controlado.

Resultado: documentar los defaults elegidos. No convertir una diferencia marginal en una regla universal.

Implementación inicial publicada en `126d519c354e6bbc70a0dae3b37ad07262248b3e`.

Completado tras la auditoría #4: `scripts/benchmark.ps1` genera una muestra de voz local temporal y `scripts/benchmark.py` mide la misma CLI y serialización de producción. En la muestra de 5.731 s, `large-v3-turbo` CUDA `float16` obtuvo RTF 0.807; `large-v3` obtuvo mayor coincidencia cualitativa con la referencia local. Se mantiene `large-v3-turbo` como perfil rápido por rendimiento, sin declarar un ganador universal de calidad.

## Fase 6 — Procesamiento por carpeta

**Estado: DONE**

Objetivo: procesar de forma repetible múltiples llamadas.

Entregables previstos:
- directorio de entrada configurable;
- directorio de salida configurable;
- manejo de errores por archivo;
- logs;
- no reprocesar accidentalmente archivos ya completados;
- resumen final de éxitos/fallos.

Completado: la CLI acepta un directorio de MP4 no recursivo, continúa tras fallos individuales, muestra un resumen y escribe `folder-run.jsonl`. Las salidas existentes se omiten salvo `--overwrite`, por lo que repetir la ejecución es segura.

## Fase 7 — Automatización recurrente

**Estado: DONE**

Objetivo: eliminar la ejecución manual cuando el flujo base sea estable.

Evaluar:
- Windows Task Scheduler;
- watcher persistente.

Se elegirá una sola opción inicial mediante una decisión documentada. No se implementará como Windows Service en el MVP.

Completado: se eligió Windows Task Scheduler frente a watcher persistente (D-021). Los scripts PowerShell crean/eliminan la tarea diaria y el runner invoca la misma CLI de carpeta, dejando `automation.log` y `folder-run.jsonl` para diagnóstico.

## Fase 8 — Release MVP

**Estado: DONE**

Objetivo: dejar una versión pública reproducible.

Entregables:
- README de instalación/uso;
- troubleshooting;
- versión fijada de dependencias;
- pruebas verdes;
- ejemplos sin datos sensibles;
- changelog/release notes;
- tag de versión.

Completado: release MVP `v0.1.0` con instalación desde clone limpio, uso, troubleshooting, changelog, dependencias fijadas y verificaciones finales. El tag se crea después de validar el clone limpio y la suite.


# v0.2.0 — GUI desktop y CLI para agentes

Las fases 0–8 corresponden al MVP v0.1.0 y permanecen cerradas. El trabajo siguiente es post-MVP.

## Fase 9 — Contrato CLI y capa de aplicación compartida

**Estado: DONE**

Objetivo: reforzar el CLI como interfaz permanente para humanos, scripts y agentes de IA antes de añadir la GUI.

Entregables:
- mantener compatibilidad con `python -m local_call_transcriber`;
- añadir un entry point CLI nominal cómodo para automatización;
- completar `--help`, códigos de salida y documentación de outputs;
- validar `docs/CLI_AGENT_USAGE.md` con una fixture;
- extraer la construcción/configuración de la operación a una capa de aplicación compartida;
- garantizar que el core/CLI no depende de PySide6.

No implementar todavía la ventana gráfica.

Completado: se mantiene `python -m local_call_transcriber` y se incorpora el
entry point nominal `local-call-transcriber`. Ambos convierten la entrada en un
`TranscriptionRequest` y llaman a `TranscriptionApplication`, sin importar
PySide6. `docs/CLI_AGENT_USAGE.md` documenta los comandos, outputs y códigos de
salida; las pruebas cubren `--help`, el flujo de una fixture y la localización
del TXT resultante.

## Fase 10 — GUI básica con PySide6

**Estado: DONE**

Objetivo: añadir una ventana desktop simple sobre el backend existente.

Entregables:
- PySide6 + Qt Widgets como dependencia GUI separable;
- selección de archivo MP4 o carpeta;
- selección de directorio de salida;
- perfiles Rápido (`large-v3-turbo`) y Calidad (`large-v3`);
- idioma auto/es/en;
- hardware Automático/GPU/CPU;
- VAD, word timestamps y overwrite;
- botón Transcribir;
- visualización de resultado/error.

La GUI debe usar la capa de aplicación compartida y no invocar el CLI como subprocess.

Completado: `local_call_transcriber.gui` implementa una ventana PySide6/Qt
Widgets opcional. Sus controles construyen un `TranscriptionRequest` y llaman
directamente a `TranscriptionApplication`; el CLI sigue sin requerir PySide6.
La instalación opcional está fijada en `requirements-gui.txt` y se habilita con
`scripts/bootstrap.ps1 -WithGui`. La ejecución permanece síncrona: no se han
implementado workers, progreso ni cancelación, que pertenecen a Fase 11.

## Fase 11 — Background, progreso y operación

**Estado: DONE**

Objetivo: hacer la GUI segura y efectiva durante trabajos largos.

Modelo de ejecución de esta fase:
- ChatGPT realiza el diseño y la implementación inicial del código, tests y documentación;
- ChatGPT publica esa implementación en GitHub;
- Codex sincroniza después `origin/main` y valida la aplicación en el equipo Windows real;
- Codex ejecuta las pruebas automatizadas y las pruebas operativas necesarias;
- Codex puede ajustar código, tests y documentación si la evidencia local lo hace pertinente para cumplir los criterios;
- ChatGPT audita finalmente los cambios publicados por Codex antes de avanzar la Fase 12.

Entregables:
- worker/`QThreadPool` o equivalente Qt;
- UI responsiva durante transcripción;
- estado por archivo y progreso global de carpeta;
- cancelación segura después del archivo actual;
- panel de log/diagnóstico;
- abrir carpeta de resultados;
- pruebas de error, carpeta y fallback.

No inventar porcentaje interno de inferencia mientras el engine no exponga progreso real.

Completado: ChatGPT implementó worker Qt, progreso real por archivo, cancelación
cooperativa, panel de diagnóstico y apertura de resultados. Codex validó la
implementación en Windows real sobre la base `34bcf83`: bootstrap GUI correcto,
29 pruebas verdes, Ruff y pip check correctos, smoke GUI real, procesamiento de
MP4, carpeta/cancelación, errores y ruta `device=auto`. El commit
`2f7084a176cf83af3c25937a9e01baa445e9de16` reforzó las pruebas de
`folder-run.jsonl` tras cancelación y de la ruta enviada a
`QDesktopServices`.

## Fase 12 — Release v0.2.0

**Estado: NEXT**

Objetivo: publicar la primera versión con GUI conservando el CLI como herramienta independiente.

Entregables:
- instalación limpia validada;
- documentación CLI y GUI;
- dependencias fijadas;
- validación de empaquetado Windows;
- suite completa verde;
- auditoría de secretos/datos sensibles;
- changelog/release notes;
- tag de versión después de las verificaciones.

Implementación inicial de ChatGPT publicada: metadata `0.2.0`, changelog y
release notes, configuración `pyside6-deploy` standalone, entrypoint de deploy
con smoke real CPU, scripts de packaging/auditoría y pruebas de metadata. La fase
permanece `NEXT` hasta que Codex complete desde un clone limpio
`docs/PHASE12_VALIDATION.md` y ChatGPT audite el resultado. El tag
`v0.2.0` no debe existir todavía.

La primera validación local de packaging se interrumpió tras detectar una cadena
de problemas específicos de Nuitka 2.6.8 y recompilaciones largas. La revisión
adopta Nuitka 4.2.1, simplifica las inclusiones y añade un build desacoplado
observable. La Fase 12 sigue en estado `NEXT`: estas correcciones requieren una
nueva validación limpia antes de crear el tag.
