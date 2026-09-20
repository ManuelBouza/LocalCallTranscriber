# Criterios de aceptación

Los criterios siguientes son normativos. Una fase no pasa a `DONE` hasta que todos sus criterios aplicables estén satisfechos o una excepción esté documentada explícitamente como decisión.

## Globales

Para toda fase:

- Windows nativo; ninguna dependencia de WSL o Docker.
- No se versionan multimedia, modelos, transcripciones, secretos ni caches.
- Las pruebas existentes siguen pasando.
- El diff ha sido revisado antes del commit.
- La documentación afectada está actualizada.
- No se avanza automáticamente a otra fase.
- Los comandos documentados funcionan en PowerShell.

## Fase 0 — Preflight

- `scripts/doctor.ps1` ejecuta sin privilegios administrativos para las comprobaciones normales.
- Informa versión de Windows.
- Informa versión de PowerShell.
- Enumera instalaciones de Python relevantes o informa que no existen.
- Informa GPU NVIDIA, driver y VRAM si son detectables.
- Informa el estado detectado de CUDA/cuDNN/CTranslate2 sin instalar nada.
- Informa espacio libre de la unidad/ruta relevante.
- Distingue claramente `PASS`, `WARN`, `FAIL` y `NOT_FOUND`.
- No modifica PATH global.
- No instala paquetes del sistema.
- Su ejecución no cambia materialmente el estado del equipo.
- Existe una prueba o validación automatizada razonable para la lógica parseable del diagnóstico.

## Fase 1 — Bootstrap

- Crea o reutiliza `.venv` de forma idempotente.
- Rechaza o informa claramente una versión Python incompatible.
- Instala herramientas de desarrollo dentro de `.venv`, no globalmente.
- Existe un comando documentado para ejecutar tests.
- Todas las pruebas pasan en CPU.
- La estrategia de versiones queda documentada.

## Fase 2 — CPU baseline

- Un MP4 válido puede transcribirse en CPU sin GPU.
- No requiere FFmpeg instalado externamente para el flujo normal.
- `device=cpu` funciona.
- `compute_type=int8` funciona o cualquier desviación queda justificada.
- Se generan TXT y JSON válidos.
- El JSON contiene al menos modelo, idioma, segmentos y timestamps.
- Los errores de archivo inexistente o formato inválido producen salida clara y código de error no cero.
- La lógica independiente del modelo tiene pruebas unitarias.

## Fase 3 — Formatos

- SRT válido.
- VTT válido.
- Segmentos ordenados cronológicamente.
- Word timestamps pueden activarse y desactivarse.
- Las rutas de salida no sobrescriben de forma silenciosa datos no relacionados.
- Pruebas automatizadas cubren serialización.

## Fase 4 — CUDA

- La aplicación sigue funcionando en CPU sin CUDA.
- `device=cuda` falla de forma explícita y accionable si CUDA no es utilizable.
- `device=auto` puede caer a CPU cuando la inicialización GPU falla.
- Se demuestra una transcripción real usando CTranslate2 sobre GPU antes de declarar CUDA `PASS`.
- La combinación validada de dependencias queda registrada.
- Se prueban los compute types compatibles seleccionados.

## Fase 5 — Benchmark

- Benchmark ejecutable y reproducible.
- Registra modelo, device, compute type y parámetros relevantes.
- Registra duración y tiempo de procesamiento.
- Calcula real-time factor.
- No publica ni versiona los audios de benchmark.
- La elección de defaults queda documentada en `docs/DECISIONS.md`.

## Fase 6 — Carpeta

- Puede procesar más de un archivo en una ejecución.
- Un fallo individual no destruye resultados de otros archivos.
- Produce resumen de éxitos y errores.
- Evita reprocesamiento accidental según una regla documentada.
- Es seguro repetir la ejecución.

## Fase 7 — Automatización

- La opción elegida se justifica en `docs/DECISIONS.md`.
- La automatización invoca el mismo CLI validado; no crea un segundo pipeline.
- Los logs permiten diagnosticar fallos.
- Existe procedimiento documentado para habilitar, deshabilitar y probar la automatización.

## Fase 8 — Release

- Instalación documentada desde un clone limpio.
- Uso básico documentado.
- Troubleshooting documentado.
- Dependencias fijadas.
- Suite de tests verde.
- No hay secretos ni datos sensibles en el historial nuevo de la release.
- Tag de versión creado solo después de las verificaciones finales.


## v0.2.0 — Fase 9 — Contrato CLI y capa compartida

- La invocación `python -m local_call_transcriber` sigue funcionando.
- Existe un entry point CLI nominal y documentado para automatización.
- `--help` documenta las opciones soportadas.
- Los códigos de salida y outputs están documentados en `docs/CLI_AGENT_USAGE.md`.
- Un agente que siga únicamente `docs/CLI_AGENT_USAGE.md` puede transcribir una fixture MP4 y localizar el TXT resultante.
- El CLI funciona sin importar PySide6.
- CLI y futura GUI pueden reutilizar una capa de aplicación compartida sin duplicar el pipeline.
- Las pruebas existentes siguen verdes.

## v0.2.0 — Fase 10 — GUI básica

- La GUI usa PySide6 + Qt Widgets.
- Puede seleccionar un MP4 o una carpeta y un directorio de salida.
- Permite escoger rápido/calidad, idioma, auto/GPU/CPU, VAD, word timestamps y overwrite.
- Los valores simples de GUI se traducen correctamente a la configuración core.
- La GUI llama a la capa de aplicación compartida, no ejecuta el CLI como subprocess.
- El CLI continúa funcionando sin PySide6 instalado.
- La GUI muestra errores accionables.

## v0.2.0 — Fase 11 — Ejecución background y UX

- La ventana no se bloquea durante una transcripción.
- Los trabajos se ejecutan fuera del hilo de eventos Qt.
- Existe estado visible por archivo y resumen para carpetas.
- Puede solicitarse cancelación segura al terminar el archivo actual.
- Puede abrirse el directorio de resultados.
- Existe un panel o superficie equivalente para logs/diagnóstico.
- Se validan archivo individual, carpeta, error y fallback CPU.

## v0.2.0 — Fase 12 — Release GUI

- Instalación desde clone limpio validada.
- Dependencias GUI fijadas y separadas del core cuando corresponda.
- CLI y GUI documentados.
- El CLI sigue pasando sus pruebas independientemente de la GUI.
- El paquete Windows standalone se construye desde la configuración versionada.
- El smoke del ejecutable empaquetado transcribe un MP4 temporal y valida TXT/JSON/SRT/VTT.
- El artefacto no contiene pesos de modelos ni datos de llamadas.
- El ejecutable GUI empaquetado abre correctamente en Windows.
- La auditoría de release no detecta multimedia/transcripciones/modelos versionados ni patrones comunes de secretos.
- Changelog/release notes actualizados.
- El tag de v0.2.0 se crea sólo después de todas las verificaciones.
