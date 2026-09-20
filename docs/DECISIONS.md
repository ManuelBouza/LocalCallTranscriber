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

## D-019 — Default basado en benchmark local

**Estado:** Aceptada

El default es `large-v3-turbo`, `device=auto` y `compute_type=auto` (CUDA `float16` cuando está disponible; CPU `int8` como fallback). Tras la auditoría #4, el benchmark ejecuta la misma CLI, engine, VAD y serialización que producción sobre una muestra de voz local temporal de 5.731 s, con referencia conocida. En la RTX 2060, `large-v3-turbo` CUDA `float16` obtuvo RTF 0.807; `large-v3` CUDA `float16` obtuvo 1.786. La coincidencia de tokens con la referencia local fue 0.800 y 0.867 respectivamente.

Estos resultados son una observación controlada y cualitativa, no una afirmación universal de calidad. `large-v3-turbo` se elige como perfil rápido por rendimiento; `large-v3` permanece disponible como perfil de calidad.

**Motivo:** `large-v3-turbo` reduce el tiempo de proceso y carga manteniendo el perfil rápido previsto. El fallback CPU conserva la disponibilidad sin CUDA.

## D-020 — Carpeta no recursiva y salidas como marca de completado

**Estado:** Aceptada

El modo carpeta procesa sólo `*.mp4` del directorio indicado. Un archivo con salidas existentes se omite salvo `--overwrite`; los errores no interrumpen el resto. Cada ejecución deja un registro JSONL y un resumen.

**Motivo:** permite repetir el proceso sin destruir resultados ni reprocesar llamadas ya terminadas.

## D-021 — Windows Task Scheduler para automatización inicial

**Estado:** Aceptada

Se evalúan dos opciones: un watcher persistente reaccionaría antes a archivos nuevos, pero requiere un proceso residente y gestión adicional de archivos todavía en copia. Windows Task Scheduler ejecuta periódicamente la CLI de carpeta ya validada, no requiere un servicio y deja logs por ejecución. Se adopta una tarea diaria configurable.

**Motivo:** es la opción más simple y recuperable para el MVP; las salidas existentes impiden reprocesos accidentales entre ejecuciones.


## D-022 — CLI permanente y apto para agentes

**Estado:** Aceptada

El CLI seguirá existiendo y disponible como interfaz de primer nivel aunque el proyecto incorpore una GUI. Debe ser utilizable por personas, scripts y agentes de IA con un contrato documentado de comandos, salidas y códigos de retorno.

La GUI será una capa superior y compartirá la lógica de aplicación con el CLI. No se permitirá que la GUI reemplace el CLI ni que el CLI dependa de bibliotecas exclusivas de GUI.

**Motivo:** conservar automatización, depuración, composición con otras herramientas y permitir solicitudes de agentes como "usa LocalCallTranscriber para extraer el texto de este MP4".

## D-023 — PySide6 + Qt Widgets para la GUI de v0.2.0

**Estado:** Aceptada

La primera GUI desktop se implementará con PySide6 y Qt Widgets. La interfaz será básica y operacional: selección de archivo/carpeta y salida, perfiles rápido/calidad, idioma, hardware, VAD, timestamps por palabra, overwrite, estado de ejecución, errores y apertura de resultados.

Los trabajos de transcripción no se ejecutarán en el hilo de eventos de Qt.

**Motivo:** PySide6 permite una aplicación desktop nativa y mantenible sobre el backend Python existente, con threading/workers y una ruta posterior de empaquetado Windows, sin introducir una arquitectura web.

## D-024 — Entry point nominal y solicitud compartida

**Estado:** Aceptada

El comando nominal de automatización es `local-call-transcriber`, conservando
como compatible `python -m local_call_transcriber`. Ambos adaptan su entrada a
`TranscriptionRequest` y usan `TranscriptionApplication`, la capa de aplicación
sin dependencias GUI que también utilizará la futura ventana.

**Motivo:** ofrece un comando instalable y predecible para humanos, scripts y
agentes, a la vez que evita duplicar el pipeline cuando se incorpore PySide6.

## D-025 — PySide6 opcional y ejecución directa de la capa de aplicación

**Estado:** Aceptada

PySide6 6.8.3 se declara como extra opcional y se instala con
`scripts/bootstrap.ps1 -WithGui`; no forma parte de las dependencias core. La
ventana Qt Widgets traduce sus controles a `TranscriptionRequest` y llama a
`TranscriptionApplication` directamente. La primera versión ejecuta de forma
síncrona; no incorpora workers, progreso ni cancelación.

**Motivo:** permite una operación desktop básica sin romper la automatización
ni añadir una dependencia GUI al CLI. Reservar la concurrencia para Fase 11
evita introducir una solución parcial de threading fuera de su alcance.


## D-026 — ChatGPT implementa; Codex valida y corrige localmente

**Estado:** Aceptada

El flujo de desarrollo post-MVP asigna a ChatGPT el diseño y la implementación inicial de cada fase. Codex se utiliza después como verificador sobre el equipo Windows real: sincroniza la implementación, ejecuta tests y pruebas operativas, inspecciona la aplicación y corrige código, tests o documentación cuando sea necesario para satisfacer la tarea.

Codex conserva libertad técnica para ajustar la solución si la evidencia local lo justifica, pero debe respetar el alcance de la fase activa y no implementar trabajo futuro innecesario. Tras su validación o correcciones, ChatGPT realiza la auditoría final antes de avanzar el plan.

**Motivo:** concentrar en Codex las tareas donde su acceso al entorno local aporta más valor y reducir el consumo de contexto/tokens en diseño e implementación que pueden realizarse previamente desde ChatGPT.


## D-027 — Progreso por archivo y cancelación cooperativa

**Estado:** Aceptada

La GUI ejecuta `TranscriptionApplication` mediante un worker Qt en
`QThreadPool`. La capa de aplicación/orchestration expone callbacks neutrales
de inicio y fin de archivo y una consulta de cancelación, sin introducir una
dependencia Qt en el core.

El progreso de carpeta se calcula únicamente con archivos realmente iniciados y
terminados. Un MP4 individual usa progreso indeterminado. La cancelación se
aplica entre archivos: el archivo actualmente en inferencia termina y se
conservan sus salidas antes de detener el lote.

**Motivo:** mantiene la ventana responsiva y evita afirmar un porcentaje interno
que faster-whisper/CTranslate2 no proporciona de forma fiable, a la vez que
preserva resultados válidos ante una cancelación.


## D-028 — pyside6-deploy standalone para la primera distribución GUI

**Estado:** Aceptada

La primera distribución Windows de la GUI usa `pyside6-deploy` de PySide6
6.8.3 con Nuitka 2.6.8 en modo `standalone`. La configuración vive en
`pysidedeploy.spec` y la construcción se orquesta mediante
`scripts/package_gui.ps1`.

La configuración de Nuitka incluye `--assume-yes-for-downloads`: en una
máquina Windows sin el compilador compatible, autoriza únicamente la descarga
cacheada del toolchain que Nuitka solicita para completar un build no
interactivo de release.

El script prepara explícitamente el MinGW64 soportado que Nuitka descarga y
exporta, sólo durante el proceso de empaquetado, su directorio de cabeceras
como `C_INCLUDE_PATH`. Con CPython oficial y ese toolchain, las rutas `-I` de
Nuitka requieren exponer la misma ruta como include de sistema para resolver
`_mingw_stdarg.h`. La variable se restaura al finalizar y no modifica PATH ni
la configuración global del equipo.

PySide6 6.8.3/Nuitka genera inicialmente `gui_main.exe` dentro del directorio
standalone. El script de release lo renombra a `LocalCallTranscriber.exe` antes
del smoke y de crear el manifiesto, de forma que el nombre público sea estable.

La configuración incluye explícitamente `av.utils` y los módulos de side-data
`av.sidedata.encparams` y `av.sidedata.motionvectors`: PyAV los resuelve de
forma dinámica, por lo que el seguimiento estático de Nuitka no basta para el
smoke ni para el arranque del ejecutable. Incluir sólo esos módulos evita un
`AssertionError` interno de Nuitka 2.6.8 al incluir el paquete PyAV completo.

El artefacto no incluye pesos Whisper ni datos de llamadas. El ejecutable
empaquetado incorpora un modo interno `--package-smoke` usado únicamente para
validación de release: genera un MP4 temporal y prueba la ruta real
`tiny/cpu/int8` y los outputs TXT/JSON/SRT/VTT.

No se adopta todavía `onefile`. Puede evaluarse después si aporta una ventaja
real sin degradar diagnóstico, tamaño, inicio o compatibilidad con las
dependencias nativas de faster-whisper/CTranslate2.

**Motivo:** Qt documenta `pyside6-deploy` como su herramienta de deployment y
el modo standalone mantiene visibles las dependencias del paquete, lo que
simplifica la primera validación y el diagnóstico en Windows.


## D-029 — Diferir mejoras de revisión y calidad hasta después de v0.2.0

**Estado:** Aceptada

Las mejoras descubiertas durante pruebas reales —progreso detallado, diagnóstico
de caché/symlinks, reproductor sincronizado, revisión humana, señales de
confianza y estrategia híbrida Turbo/large-v3— se documentan en
`docs/POST_V020_QUALITY_REVIEW.md` y quedan fuera del release candidate
v0.2.0 actualmente en validación.

No se modificarán los defaults de v0.2.0 basándose en una única llamada real.
Las observaciones deben revisarse y validarse sobre más muestras antes de
convertirse en política permanente.

**Motivo:** preservar la estabilidad y reproducibilidad de la release que ya está
siendo validada, sin perder los hallazgos de calidad obtenidos con audio real.
