# Validación local de la Fase 11

Este documento es la checklist para Codex después de la implementación inicial
de ChatGPT. Codex puede modificar código, tests y documentación si la evidencia
local demuestra que es necesario.

## Preparación

Desde PowerShell en la raíz del repositorio:

```powershell
git pull --ff-only origin main
.\scripts\bootstrap.ps1 -WithGui
```

## Validación automatizada obligatoria

```powershell
.\scripts\test.ps1
.\.venv\Scripts\python.exe -m pip check
```

La suite debe cubrir al menos:

- CLI sin dependencia PySide6;
- traducción de controles GUI a `TranscriptionRequest`;
- ejecución del worker sin bloquear la llamada de UI;
- progreso de carpeta;
- cancelación después del archivo actual;
- propagación de errores;
- comportamiento existente de fallback `auto -> cpu`.

## Smoke GUI local

Lanza:

```powershell
.\.venv\Scripts\python.exe -m local_call_transcriber.gui
```

Verifica en Windows real:

1. la ventana abre sin consola de error;
2. puede seleccionarse un MP4 y un directorio de salida;
3. al pulsar **Transcribir**, la ventana sigue respondiendo mientras procesa;
4. se muestra el archivo actual;
5. para un único MP4 la barra es indeterminada mientras trabaja y finaliza al terminar;
6. el panel de diagnóstico recibe mensajes útiles;
7. **Abrir resultados** abre el directorio correcto;
8. un error de entrada o engine aparece en la GUI sin cerrar la aplicación.

## Smoke de carpeta y cancelación

Usa una carpeta local con al menos dos MP4 de prueba no sensibles.

Verifica:

1. el progreso global usa archivos procesados/total;
2. los resultados por archivo se conservan;
3. solicita **Cancelar después del actual** mientras el primer archivo está en proceso;
4. el archivo actual termina normalmente;
5. no se inicia el siguiente archivo;
6. `folder-run.jsonl` contiene el resultado del archivo terminado;
7. la GUI queda reutilizable para iniciar otra operación.

## Hardware

Con **Automático**, confirma que se conserva la ruta existente
`device=auto, compute_type=auto`. Si CUDA falla de forma controlada, la ruta
existente debe poder caer a CPU sin bloquear la GUI.

No cambies la política CUDA validada salvo que una prueba real revele un defecto.

## Resultado esperado de Codex

Si todo pasa, reporta:

- commit base validado;
- pruebas ejecutadas y resultados;
- smoke GUI realizado;
- smoke de cancelación realizado;
- hardware/fallback observado;
- si hubo cambios, commit/push y resumen exacto.

No marques Fase 11 como DONE ni avances Fase 12; ChatGPT realiza la auditoría y
la transición final.
