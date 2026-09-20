# Validación local de la Fase 12

Esta checklist valida el release candidate `v0.2.0` después de la implementación
inicial de ChatGPT. Codex puede ajustar código, scripts, tests o documentación si
la evidencia local lo requiere.

No crear el tag `v0.2.0`. La creación del tag corresponde a la auditoría final
posterior de ChatGPT.

## 1. Clone limpio

Trabaja en un directorio nuevo, no sobre el checkout de desarrollo existente:

```powershell
git clone https://github.com/ManuelBouza/LocalCallTranscriber.git LocalCallTranscriber-v020-verify
Set-Location .\LocalCallTranscriber-v020-verify
git status --short
```

El árbol debe comenzar limpio.

## 2. Bootstrap completo

```powershell
.\scripts\bootstrap.ps1 -WithGui
```

Confirma:

- CPython 3.11.x;
- paquete instalado como versión `0.2.0`;
- PySide6 6.8.3;
- CLI nominal disponible;
- GUI nominal disponible.

## 3. Suite y dependencias

```powershell
.\scripts\test.ps1
.\.venv\Scripts\python.exe -m pip check
```

Todo debe quedar verde. El CLI debe seguir funcionando sin depender del arranque
de la GUI.

## 4. Dry-run del deploy

```powershell
.\scripts\package_gui.ps1 -DryRun
```

Revisa el comando de Nuitka generado. La ruta elegida es
`pyside6-deploy`/Nuitka, modo `standalone`.

Si `dumpbin.exe` no está disponible, registra el warning y determina si la
compilación real puede continuar correctamente en el equipo. Qt recomienda
`dumpbin`/MSVC para el análisis eficiente de dependencias en Windows.

## 5. Auditoría y build real

Con el árbol todavía limpio:

```powershell
.\scripts\release_audit.ps1
```

Debe:

- ejecutar nuevamente tests/preflight;
- pasar `pip check`;
- comprobar que no hay multimedia/transcripciones/modelos versionados;
- comprobar patrones comunes de secretos;
- confirmar que el tag `v0.2.0` aún no existe;
- construir el paquete Windows;
- ejecutar automáticamente el smoke `--package-smoke`;
- rechazar pesos de modelos dentro del paquete;
- generar `dist\package-manifest.json`.

Conserva del manifest:

- ruta del ejecutable;
- SHA-256;
- file count;
- total bytes.

## 6. Ejecutable empaquetado

Lanza el `LocalCallTranscriber.exe` encontrado por el manifest.

Comprueba en Windows real:

1. abre la ventana Qt sin Python visible ni traceback;
2. los controles de Fase 10/11 están presentes;
3. la ventana sigue siendo responsiva;
4. no aparece una consola adicional como interfaz normal;
5. cerrar la aplicación termina el proceso normalmente.

El smoke no interactivo ya valida dentro del paquete una transcripción real con
MP4 temporal, `tiny`, CPU `int8` y outputs TXT/JSON/SRT/VTT.

## 7. CLI después del empaquetado

El empaquetado no debe alterar el CLI del checkout:

```powershell
.\.venv\Scripts\local-call-transcriber.exe --help
.\.venv\Scripts\python.exe -m local_call_transcriber --help
```

Ambos deben seguir operativos y equivalentes.

## 8. Integridad del repositorio

Al finalizar:

```powershell
git status --short
git tag --list v0.2.0
```

`dist/` y los artefactos Nuitka deben permanecer ignorados. El árbol versionado
debe seguir limpio y el tag debe seguir ausente.

## Reporte esperado de Codex

Reporta:

- commit exacto validado;
- clone limpio: PASS/FAIL;
- bootstrap: PASS/FAIL;
- número de tests;
- Ruff/pip check/preflight;
- dry-run deploy;
- build standalone;
- package smoke;
- manifest (SHA-256, files, bytes);
- lanzamiento real de la GUI empaquetada;
- CLI posterior al build;
- auditoría de datos/secretos;
- limitaciones observadas;
- cambios realizados, si los hubo, con commit/push.

No marques la Fase 12 como DONE y no crees el tag.
