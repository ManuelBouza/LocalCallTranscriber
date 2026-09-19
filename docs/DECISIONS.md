# Decisiones técnicas

Este documento registra decisiones que condicionan el proyecto. Cambiar una decisión aceptada requiere añadir una nueva entrada que la sustituya; no borrar el historial.

## D-001 — Windows 11 nativo

**Estado:** Aceptada

El entorno objetivo es Windows 11 nativo con PowerShell.

WSL y Docker quedan fuera del flujo soportado inicial.

**Motivo:** el proyecto debe ejecutarse directamente en el mismo entorno donde Codex y el usuario operarán los archivos locales.

## D-002 — Procesamiento local y gratuito

**Estado:** Aceptada

La transcripción normal no utilizará APIs cloud.

**Motivo:** privacidad de llamadas, ausencia de cuota por minuto y requisito de coste recurrente cero.

## D-003 — faster-whisper como primer motor

**Estado:** Aceptada

El primer adaptador será `faster-whisper`, manteniéndolo detrás de una interfaz de engine.

**Motivo:** buen rendimiento local, CTranslate2, soporte CPU/GPU y uso de PyAV.

## D-004 — CPU obligatoria; CUDA opcional

**Estado:** Aceptada

La aplicación debe funcionar en CPU. CUDA será aceleración opcional.

`auto` deberá poder degradar a CPU ante un fallo GPU.

**Motivo:** evitar que una instalación o actualización CUDA deje inutilizable la herramienta.

## D-005 — Sin FFmpeg externo para el pipeline básico

**Estado:** Aceptada

La transcripción MP4 utilizará la decodificación disponible mediante PyAV/faster-whisper.

**Motivo:** reducir dependencias globales en Windows.

Una función futura puede requerir FFmpeg, pero deberá aprobarse explícitamente.

## D-006 — Dos perfiles iniciales de modelo

**Estado:** Aceptada

- calidad: `large-v3`;
- rápido: `large-v3-turbo`.

El default se escogerá mediante benchmark local, no por intuición.

## D-007 — TOML para configuración

**Estado:** Aceptada

La configuración persistente utilizará TOML.

**Motivo:** formato legible, simple y adecuado para configuración estructurada.

## D-008 — GitHub como fuente de verdad

**Estado:** Aceptada

Las instrucciones relevantes deben persistirse en el repositorio. Los prompts a Codex deben ser mínimos y referenciar la documentación versionada.

**Motivo:** permitir que usuario, Codex y revisores trabajen sobre el mismo contrato verificable y no dependan del contexto de un chat.

## D-009 — Diarización fuera del MVP

**Estado:** Aceptada

La separación automática de hablantes no se implementará dentro del MVP de faster-whisper.

**Motivo:** mantener la primera versión enfocada y no introducir todavía pyannote/WhisperX y sus dependencias adicionales.

## D-010 — Preflight antes de cambios CUDA

**Estado:** Aceptada

No se instalarán ni modificarán CUDA, cuDNN o PATH global antes de completar el preflight.

**Motivo:** primero debe conocerse el hardware y el estado real de las dependencias para evitar combinaciones incompatibles.

## D-011 — Versiones validadas antes de fijar GPU

**Estado:** Aceptada

`faster-whisper 1.2.1` es el candidato inicial de investigación, pero la combinación definitiva de faster-whisper, CTranslate2, CUDA y cuDNN se fijará únicamente después de pruebas reales en Windows.

**Motivo:** las compatibilidades GPU dependen de versiones concretas y deben demostrarse en el equipo objetivo.

## D-012 — Preflight de solo lectura en PowerShell

**Estado:** Aceptada

El preflight se implementa como `scripts/doctor.ps1`. Consulta el estado del equipo y puede emitir un informe JSON, pero no instala software ni modifica `PATH` u otra configuración del sistema.

**Motivo:** disponer de evidencia reproducible del entorno antes de elegir o modificar la ruta CUDA, conservando un flujo seguro en CPU.

## D-013 — Diagnóstico independiente de toolkit y runtime CUDA

**Estado:** Aceptada

El preflight informa por separado el toolkit CUDA (`nvcc`) y las bibliotecas de runtime requeridas habitualmente por CTranslate2 (`cudart`, cuBLAS y cuDNN). También comprueba CTranslate2 en cada intérprete detectado por el launcher de Python o el `PATH`.

**Motivo:** un toolkit no prueba que el runtime sea utilizable, y CTranslate2 puede estar instalado fuera del intérprete Python prioritario del proceso.

## D-014 — Bootstrap local con herramientas de desarrollo fijadas

**Estado:** Aceptada

El entorno de desarrollo se crea en `.venv` mediante `scripts/bootstrap.ps1`. `requirements-dev.txt` fija las dependencias directas y transitivas de desarrollo, incluidas setuptools, pytest y Ruff; el paquete se instala en modo editable sin instalar motores de transcripción todavía. Cualquier actualización del lock requiere una ejecución verde de `scripts/test.ps1`.

**Motivo:** obtener un ciclo de pruebas reproducible sin modificar Python global ni fijar prematuramente dependencias de CPU/GPU que requieren validación posterior.

## D-015 — CPython 3.11.x como baseline validado del MVP

**Estado:** Aceptada

La ruta normal de bootstrap y pruebas usa CPython 3.11.x, seleccionado explícitamente mediante el launcher `py`. Una `.venv` de otro minor no se reutiliza silenciosamente. La metadata del paquete conserva el mínimo `>=3.11` para que `-PythonExecutable` pueda crear e instalar entornos experimentales de minors posteriores, pero no cambia el baseline ni habilita la ruta normal de pruebas.

**Motivo:** faster-whisper estable aún no declara soporte integrado para Python 3.14; fijar 3.11 evita que el MVP dependa de un minor no validado solo por aparecer primero en `PATH`.

## D-016 — Baseline CPU faster-whisper con int8

**Estado:** Aceptada

La primera ruta de transcripción usa `faster-whisper 1.2.1`, CTranslate2 `4.8.2` y PyAV `18.1.0` con `device=cpu` y `compute_type=int8`. PyAV se usa para decodificar MP4 sin una instalación externa de FFmpeg. El modelo inicial de smoke test es `tiny` y se almacena fuera del repositorio.

**Motivo:** ofrece una ruta local verificable y compatible con equipos sin CUDA antes de evaluar aceleración GPU o modelos de mayor calidad.

## D-017 — Salidas ordenadas y sobrescritura explícita

**Estado:** Aceptada

Las salidas SRT y VTT se generan junto a TXT y JSON, ordenadas por timestamp inicial. Los timestamps por palabra se solicitan con `--word-timestamps`. El CLI no sustituye salidas existentes salvo que se indique `--overwrite`.

**Motivo:** preservar resultados previos y ofrecer formatos interoperables sin asumir que es seguro reemplazar transcripciones existentes.

## D-018 — Ruta CUDA validada con fallback en proceso

**Estado:** Aceptada

La ruta GPU usa CUDA Toolkit 12.6, cuDNN 9.11.0.98 para CUDA 12, faster-whisper 1.2.1 y CTranslate2 4.8.2. `device=cuda` devuelve un error con instrucciones de diagnóstico cuando no puede inicializarse. `device=auto` intenta CUDA y, si falla durante la inicialización, continúa en CPU con `int8` y muestra un aviso. Se validaron transcripciones reales locales en una RTX 2060 con `float16` e `int8_float16`.

**Motivo:** la aceleración es útil pero nunca puede impedir el funcionamiento CPU. Las DLL se añaden sólo al proceso para evitar depender de que una terminal herede cambios de PATH.
