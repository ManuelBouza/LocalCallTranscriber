# LocalCallTranscriber

Aplicación local para Windows 11 orientada a la transcripción de archivos de llamadas, inicialmente MP4. Todo el procesamiento se realizará localmente.

## Estado

Este repositorio contiene únicamente la estructura inicial del proyecto. Aún no implementa ningún motor de transcripción ni instala dependencias del sistema.

La primera integración prevista es `faster-whisper`. La estructura de `src/local_call_transcriber/engines` permitirá incorporar otros motores posteriormente sin rehacer la aplicación.

## Requisitos de plataforma

- Windows 11 nativo
- PowerShell para automatización y scripts
- Python mediante el entorno virtual `.venv`
- Funcionamiento en CPU como ruta compatible, incluso cuando CUDA no esté disponible

## Estructura

```text
src/local_call_transcriber/
  engines/     # Adaptadores de motores de transcripción
tests/         # Pruebas automatizadas
scripts/       # Automatización en PowerShell
```

No se versionan modelos, archivos multimedia, entornos virtuales ni resultados de transcripción.
