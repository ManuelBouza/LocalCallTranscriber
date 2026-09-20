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

## Modelo de trabajo ChatGPT + Codex

El flujo normal del proyecto es:

1. ChatGPT diseña la solución y realiza la implementación inicial del código, tests y documentación de la fase activa.
2. ChatGPT hace commit/push de esa implementación en GitHub.
3. Codex sincroniza `origin/main` y actúa principalmente como **verificador local y corrector** en el equipo Windows real.
4. Codex ejecuta las pruebas automatizadas y las verificaciones locales aplicables, incluida la aplicación real cuando el criterio requiera comportamiento que no puede validarse sólo por inspección.
5. Codex tiene libertad para modificar código, tests y documentación cuando sea necesario para que la tarea y sus criterios de aceptación se cumplan correctamente.
6. Codex debe conservar el alcance de la fase activa y evitar rediseños o trabajo futuro no necesario.
7. Si realiza ajustes, Codex revisa el diff, hace commit/push y reporta exactamente qué validó y qué cambió.
8. ChatGPT audita el resultado publicado contra los criterios y decide si corresponde avanzar la siguiente fase.

### Prioridad operativa de Codex

Codex no debe rehacer por defecto el trabajo de diseño ya implementado por ChatGPT. Su prioridad es obtener evidencia local de que la solución funciona y corregir únicamente lo necesario.

Puede apartarse de la implementación de ChatGPT cuando las pruebas, el comportamiento real de Windows, la mantenibilidad o los criterios de aceptación demuestren que un ajuste es pertinente.

El objetivo de este reparto es reservar el contexto y los tokens de Codex para aquello que aporta valor diferencial: ejecución local, interacción con la aplicación, diagnóstico real, pruebas y correcciones.
