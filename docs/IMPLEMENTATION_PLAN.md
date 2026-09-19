# Plan de implementación

Este documento define el orden obligatorio de trabajo. Codex debe ejecutar únicamente la primera fase con estado `NEXT`, salvo instrucción explícita diferente.

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

**Estado: PENDING**

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

## Fase 3 — Formatos y timestamps

**Estado: PENDING**

Objetivo: completar las salidas de usuario.

Entregables previstos:
- SRT;
- VTT;
- timestamps por segmento;
- timestamps por palabra configurables;
- validación de nombres/rutas de salida;
- pruebas de serialización.

## Fase 4 — Aceleración CUDA opcional

**Estado: PENDING**

Objetivo: habilitar GPU sin romper CPU.

Entregables previstos:
- validación real de CTranslate2 sobre CUDA;
- diagnóstico accionable de incompatibilidades;
- `device=auto|cuda|cpu`;
- fallback `cuda -> cpu` en modo auto;
- pruebas de `float16` e `int8_float16`;
- documentación exacta de la combinación validada de driver/runtime/librerías.

Las instalaciones de CUDA/cuDNN que sean necesarias deberán estar justificadas por el preflight y ser explícitas.

## Fase 5 — Benchmark y defaults

**Estado: PENDING**

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

## Fase 6 — Procesamiento por carpeta

**Estado: PENDING**

Objetivo: procesar de forma repetible múltiples llamadas.

Entregables previstos:
- directorio de entrada configurable;
- directorio de salida configurable;
- manejo de errores por archivo;
- logs;
- no reprocesar accidentalmente archivos ya completados;
- resumen final de éxitos/fallos.

## Fase 7 — Automatización recurrente

**Estado: PENDING**

Objetivo: eliminar la ejecución manual cuando el flujo base sea estable.

Evaluar:
- Windows Task Scheduler;
- watcher persistente.

Se elegirá una sola opción inicial mediante una decisión documentada. No se implementará como Windows Service en el MVP.

## Fase 8 — Release MVP

**Estado: PENDING**

Objetivo: dejar una versión pública reproducible.

Entregables:
- README de instalación/uso;
- troubleshooting;
- versión fijada de dependencias;
- pruebas verdes;
- ejemplos sin datos sensibles;
- changelog/release notes;
- tag de versión.
