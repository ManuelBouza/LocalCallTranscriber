# Requisitos

## Objetivo

LocalCallTranscriber debe transcribir llamadas almacenadas localmente, inicialmente en archivos MP4, utilizando procesamiento local y gratuito sobre Windows 11.

## Alcance inicial

El primer motor será `faster-whisper`. La arquitectura debe permitir incorporar otros motores en el futuro sin reescribir la aplicación.

La diarización de hablantes no forma parte del MVP. Podrá añadirse posteriormente como capacidad separada.

## Requisitos funcionales

### FR-001 — Entrada MP4
La aplicación debe aceptar al menos archivos `.mp4` locales como entrada.

### FR-002 — Procesamiento local
La extracción y transcripción del contenido deben ejecutarse localmente. Ningún audio, vídeo o texto de la llamada debe enviarse a un servicio cloud para completar la transcripción.

### FR-003 — CLI
Debe existir una interfaz de línea de comandos utilizable desde PowerShell.

El CLI es permanente y debe seguir disponible aunque exista una GUI. Debe poder ser utilizado directamente por humanos, scripts y agentes de IA. Su uso, opciones, salidas y códigos de salida deben estar documentados de forma suficiente para automatizar tareas como "extraer el texto de este MP4" sin depender de la GUI.

### FR-004 — Salidas
Para una transcripción completa deben poder generarse:
- TXT legible;
- JSON estructurado;
- SRT;
- VTT.

### FR-005 — Idioma
Debe permitirse:
- detección automática del idioma;
- fijar explícitamente el idioma, por ejemplo `es` o `en`.

### FR-006 — VAD
Debe poder utilizarse detección de actividad de voz para reducir procesamiento innecesario de silencios.

### FR-007 — Timestamps
Los segmentos deben incluir timestamps. Los timestamps por palabra deben ser configurables y no obligatorios.

### FR-008 — Selección de modelo
Debe existir una configuración explícita del modelo. Como mínimo se contemplarán:
- perfil de calidad: `large-v3`;
- perfil rápido: `large-v3-turbo`.

El modelo predeterminado definitivo se decidirá mediante benchmarks reproducibles sobre el hardware real.

### FR-009 — Dispositivo
Debe permitirse `auto`, `cpu` y `cuda`.

En modo `auto`, un fallo de CUDA no debe impedir continuar por CPU.

### FR-010 — Configuración
La configuración persistente de usuario debe usar un formato de texto versionable y legible. El formato elegido es TOML.

### FR-011 — Procesamiento por carpeta
Tras validar la transcripción individual, debe poder procesarse una carpeta de entrada de forma repetible.

### FR-012 — Registro
Cada ejecución debe poder registrar modelo, dispositivo, compute type, idioma, duración y tiempo de procesamiento suficientes para diagnóstico y benchmark.

### FR-013 — GUI desktop opcional
La versión post-MVP incorporará una GUI desktop básica para operar archivos y carpetas, seleccionar perfil, idioma, hardware y opciones de transcripción, ejecutar trabajos y consultar estado/errores.

La GUI es una capa de presentación. No sustituye el CLI y debe reutilizar la misma capa de aplicación y orchestration.

### FR-014 — Contrato para agentes de IA
Debe existir documentación específica para agentes de IA que defina al menos:
- invocación del CLI;
- rutas de entrada y salida;
- forma de localizar el TXT producido;
- códigos de salida;
- comportamiento ante resultados existentes;
- uso de archivo frente a carpeta;
- reglas de privacidad y de `--overwrite`.

La documentación normativa de este contrato es `docs/CLI_AGENT_USAGE.md`.

## Requisitos no funcionales

### NFR-001 — Plataforma
Windows 11 nativo. No depender de WSL ni Docker.

### NFR-002 — PowerShell
Bootstrap, diagnóstico y automatización de sistema deben estar disponibles mediante PowerShell.

### NFR-003 — Python
El proyecto requiere Python 3.11 o superior y debe ejecutarse dentro de `.venv`.

El baseline validado y soportado del MVP es CPython 3.11.x. Las versiones menores posteriores cumplen el mínimo de metadata y pueden evaluarse únicamente como experimentos controlados; no habilitan la ruta normal de pruebas ni quedan soportadas hasta que el stack de transcripción esté validado explícitamente en ellas.

### NFR-004 — CPU obligatoria
La aplicación debe funcionar sin GPU NVIDIA.

La ruta CPU utilizará inicialmente `int8`, salvo que las pruebas demuestren una alternativa claramente superior y se documente la decisión.

### NFR-005 — GPU opcional
Cuando exista una GPU NVIDIA compatible, se evaluarán al menos `float16` e `int8_float16`.

### NFR-006 — Reproducibilidad
Las dependencias utilizadas en una versión estable deben quedar fijadas de forma reproducible después de validarse en el equipo objetivo.

### NFR-007 — Privacidad
No versionar ni subir:
- llamadas;
- audios;
- vídeos;
- transcripciones;
- modelos descargados;
- secretos o tokens.

### NFR-008 — Coste
El flujo normal de transcripción no debe requerir APIs o servicios de pago.

### NFR-009 — Pruebas
La lógica que no dependa físicamente de un modelo pesado o GPU debe disponer de pruebas automatizadas. Las rutas CPU/GPU deben tener pruebas de integración o smoke tests cuando la fase correspondiente las implemente.

### NFR-010 — Observabilidad
Los fallos de dependencias, modelo, archivos y aceleración deben producir mensajes accionables y códigos de salida adecuados.

### NFR-011 — Independencia CLI/GUI
El CLI debe funcionar sin instalar ni importar dependencias exclusivas de GUI. Las dependencias de interfaz gráfica deben permanecer separadas del runtime core cuando sea razonable.

### NFR-012 — Automatización estable
La evolución de la GUI no debe romper silenciosamente comandos CLI documentados. Los cambios incompatibles del contrato CLI requieren decisión explícita, documentación y estrategia de compatibilidad.

## Fuera del alcance del MVP v0.1.0

- GUI (incorporada posteriormente en el plan v0.2.0).
- Servicios cloud de transcripción.
- WSL.
- Docker.
- diarización de hablantes;
- traducción automática;
- edición manual de subtítulos;
- Windows Service.

Estas capacidades solo se incorporarán mediante una decisión y una fase explícita posterior.
