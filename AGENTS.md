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
3. Codex sincroniza `origin/main` y actúa por defecto como **verificador local de solo validación** en el equipo Windows real.
4. Codex ejecuta las pruebas automatizadas y las verificaciones locales aplicables, incluida la aplicación real cuando el criterio requiera comportamiento que no puede validarse sólo por inspección.
5. Si Codex encuentra un defecto que exige modificar código, tests, configuración o documentación, debe detener esa parte de la validación, reportar la evidencia y proponer la corrección. **No modifica el repositorio salvo que el prompt de esa ejecución lo autorice expresamente.**
6. ChatGPT implementa normalmente las correcciones derivadas de la evidencia local y publica una nueva revisión.
7. Codex revalida la revisión publicada.
8. ChatGPT audita la evidencia final contra los criterios y decide si corresponde avanzar la siguiente fase.

### Prioridad operativa de Codex

Codex no debe rehacer por defecto el trabajo de diseño o implementación ya realizado por ChatGPT. Su prioridad es obtener evidencia local reproducible: ejecutar, observar, diagnosticar y reportar.

La autorización para corregir no se hereda de sesiones anteriores ni se presume por el hecho de encontrar un fallo. Debe aparecer explícitamente en el prompt activo.

Para operaciones largas que puedan desacoplarse, especialmente builds de packaging, Codex no debe permanecer esperando su finalización. Debe utilizar el mecanismo versionado de ejecución desacoplada, reportar PID/rutas de estado y log, y terminar el turno. La inspección posterior se reanuda únicamente cuando el usuario confirme que el proceso terminó.

El objetivo de este reparto es reservar el contexto y los tokens de Codex para aquello que aporta valor diferencial: ejecución local, interacción con la aplicación, diagnóstico y evidencia verificable.
