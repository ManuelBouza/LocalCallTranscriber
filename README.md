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
