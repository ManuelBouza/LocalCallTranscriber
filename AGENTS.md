# Instrucciones permanentes para Codex

Este repositorio es la fuente de verdad del proyecto. Antes de realizar cambios, lee este archivo y la documentación aplicable bajo `docs/`.

## Orden de autoridad

1. `AGENTS.md`: reglas operativas permanentes.
2. `docs/REQUIREMENTS.md`: requisitos funcionales y no funcionales.
3. `docs/ARCHITECTURE.md`: arquitectura y restricciones técnicas.
4. `docs/IMPLEMENTATION_PLAN.md`: fases, orden de ejecución y estado.
5. `docs/ACCEPTANCE_CRITERIA.md`: criterios objetivos de cierre.
6. `docs/DECISIONS.md`: decisiones técnicas adoptadas y su justificación.

Si dos documentos parecen contradecirse, no improvises: conserva el comportamiento existente, documenta la discrepancia y detén esa parte del cambio hasta que se resuelva.

## Reglas permanentes

- Trabaja exclusivamente en Windows 11 nativo.
- Utiliza PowerShell para automatización y scripts.
- No utilices WSL ni Docker.
- Python debe ejecutarse mediante el entorno virtual local `.venv`.
- El procesamiento de llamadas debe ser local; no subas audio, vídeo ni transcripciones a servicios externos.
- Mantén siempre una ruta funcional en CPU aunque CUDA no esté disponible.
- CUDA/GPU es una aceleración opcional, nunca un requisito para que la aplicación funcione.
- El CLI es una interfaz permanente y de primer nivel. Ninguna GUI puede sustituirlo, ocultarlo ni convertirlo en una dependencia de la GUI.
- Mantén el CLI apto para automatización por humanos, scripts y agentes de IA: comandos, opciones, outputs y códigos de salida deben estar documentados y ser predecibles.
- La GUI debe ser una capa superior opcional sobre la misma lógica de aplicación que usa el CLI; no debe implementar un segundo pipeline ni requerir lanzar el CLI como subprocess para transcribir.
- El funcionamiento del CLI no puede depender de que PySide6 u otras dependencias exclusivas de GUI estén instaladas.
- No añadas al repositorio modelos, audios, vídeos, transcripciones, secretos, credenciales, `.venv`, caches ni otros archivos pesados.
- No realices cambios globales del sistema, instalaciones de CUDA/cuDNN ni modificaciones de PATH salvo que la fase activa lo requiera expresamente.
- Ejecuta las pruebas y verificaciones exigidas por los criterios de aceptación antes de considerar completada una fase.
- Actualiza la documentación cuando una modificación cambie requisitos, arquitectura, comportamiento, comandos o decisiones técnicas.
- Ejecuta únicamente la fase pendiente indicada en `docs/IMPLEMENTATION_PLAN.md`; no avances a la siguiente sin instrucción explícita.
- Antes de hacer commit, revisa el diff y confirma que no contiene multimedia, modelos, secretos ni artefactos generados.
- Cuando una fase termine correctamente, actualiza su estado en `docs/IMPLEMENTATION_PLAN.md` en el mismo cambio.

## Flujo esperado para Codex

Para cada tarea:

1. Lee las especificaciones aplicables.
2. Identifica la fase activa.
3. Implementa solo el alcance de esa fase.
4. Ejecuta sus pruebas y criterios de aceptación.
5. Corrige los incumplimientos detectados.
6. Actualiza documentación si corresponde.
7. Revisa el diff.
8. Haz commit y push únicamente cuando los criterios de aceptación estén satisfechos.
