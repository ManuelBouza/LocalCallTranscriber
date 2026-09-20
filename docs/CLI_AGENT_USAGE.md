# Uso del CLI por agentes de IA

Este documento define cómo utilizar LocalCallTranscriber como herramienta local desde un agente de IA, un script o una terminal.

## Principio

El CLI es una interfaz permanente del proyecto. La GUI es una capa superior opcional y no sustituye el CLI.

Un agente debe poder recibir una instrucción como:

> Usa el CLI de LocalCallTranscriber para extraer el texto de este MP4.

y completar la tarea sin conocer detalles internos de faster-whisper.

## Requisitos

- Windows 11 nativo.
- Repositorio clonado.
- Entorno `.venv` preparado con `.\scripts\bootstrap.ps1`.
- El audio, vídeo y las transcripciones permanecen locales.

## Invocación estable disponible en v0.1.0

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe -m local_call_transcriber "<INPUT>" --output-dir "<OUTPUT_DIR>"
```

`<INPUT>` puede ser:

- un archivo MP4;
- un directorio que contenga MP4 directamente, sin recorrido recursivo.

Usar rutas absolutas o rutas claramente resueltas y entre comillas.

## Extraer el texto de un MP4

Ejemplo:

```powershell
.\.venv\Scripts\python.exe -m local_call_transcriber "C:\Calls\call-001.mp4" --output-dir "C:\Calls\transcripts"
```

Si termina correctamente, el texto solicitado está en:

```text
C:\Calls\transcripts\call-001.txt
```

También se generan:

```text
call-001.json
call-001.srt
call-001.vtt
```

Para una solicitud de "extraer el texto", el agente debe leer el archivo `.txt` generado. No debe intentar reconstruir la transcripción desde stdout.

## Procesar una carpeta

```powershell
.\.venv\Scripts\python.exe -m local_call_transcriber "C:\Calls\incoming" --output-dir "C:\Calls\transcripts"
```

El agente debe consultar:

- los `*.txt` generados;
- `folder-run.jsonl` para conocer el estado de cada MP4.

## Opciones principales

```text
--model large-v3-turbo   Perfil rápido y valor predeterminado.
--model large-v3         Perfil de calidad.
--language es            Fuerza español.
--language en            Fuerza inglés.
                         Si se omite, el idioma se detecta automáticamente.
--device auto            Ruta recomendada; intenta CUDA y cae a CPU.
--device cuda            Exige CUDA utilizable.
--device cpu             Fuerza CPU.
--compute-type auto      Recomendado con device=auto.
--compute-type float16   Ruta GPU validada.
--compute-type int8      Ruta CPU validada.
--word-timestamps        Incluye timestamps por palabra en JSON.
--no-vad                 Desactiva VAD.
--overwrite              Sustituye resultados existentes.
```

## Códigos de salida

- `0`: ejecución correcta. En modo carpeta también puede haber elementos `skipped` sin que sea un fallo global.
- `2`: error de entrada o validación.
- `3`: error de transcripción; en modo carpeta indica que al menos un archivo falló.

El agente debe esperar a que termine el proceso y comprobar el código de salida antes de consumir los resultados.

## Reglas para agentes

1. No subir el MP4, audio ni la transcripción a servicios externos.
2. No usar `--overwrite` salvo que el usuario pida explícitamente sustituir resultados existentes o la tarea lo requiera inequívocamente.
3. Mantener `--device auto --compute-type auto` salvo que exista una razón concreta para forzar hardware.
4. Para "extraer el texto", leer el `.txt` producido.
5. Para datos estructurados o timestamps, leer el `.json`.
6. Para subtítulos, usar `.srt` o `.vtt`.
7. Si el proceso devuelve código distinto de cero, informar del error; no afirmar que la transcripción se completó.
8. En modo carpeta, revisar `folder-run.jsonl` en vez de asumir que todos los archivos terminaron correctamente.
9. No depender de la GUI para automatización.
10. No parsear mensajes humanos de stdout como API estable si existe un archivo de salida estructurado.

## Ejemplo de flujo de un agente

Solicitud:

```text
Usa LocalCallTranscriber para extraer el texto de C:\Temp\meeting.mp4.
```

Procedimiento:

```powershell
New-Item -ItemType Directory -Path "C:\Temp\meeting-transcript" -Force | Out-Null
.\.venv\Scripts\python.exe -m local_call_transcriber "C:\Temp\meeting.mp4" --output-dir "C:\Temp\meeting-transcript"
```

Si el código de salida es `0`, leer:

```text
C:\Temp\meeting-transcript\meeting.txt
```

y utilizar ese contenido para responder a la tarea del usuario.

## Evolución prevista en v0.2

La fase de contrato CLI añadirá un entry point nominal más cómodo para automatización sin romper la invocación anterior. La forma `python -m local_call_transcriber` seguirá siendo compatible.

La GUI de v0.2 utilizará la misma capa de aplicación que el CLI y no será requisito para ejecutar el CLI.
