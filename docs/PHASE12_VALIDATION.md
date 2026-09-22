# Validación local de la Fase 12

Esta checklist valida el release candidate `v0.2.0` después de la implementación
de ChatGPT. Codex actúa por defecto como verificador local: si encuentra un
defecto que exige modificar código, tests, configuración o documentación, debe
reportarlo y detenerse. No hará cambios salvo autorización explícita en el prompt
activo.

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

Confirma CPython 3.11.x, paquete 0.2.0, PySide6 6.8.3 y ambos entry points.

## 3. Suite y dependencias

```powershell
.\scripts\test.ps1
.\.venv\Scripts\python.exe -m pip check
```

Todo debe quedar verde.

## 4. Dry-run y preflight de release

```powershell
.\scripts\package_gui.ps1 -DryRun
.\scripts\release_audit.ps1 -SkipPackage
```

La ruta elegida es `pyside6-deploy`/Nuitka 4.2.1 en modo `standalone`.
No deben aparecer los workarounds retirados de Nuitka 2.6.8:
`--disable-cache=ccache`, `--include-package=numpy` ni includes manuales
`av.*`. La configuración debe incluir `--include-package=huggingface_hub.utils`
y no debe incluir `--include-package=huggingface_hub` completo. Debe incluir además
`--include-package-data=faster_whisper` para conservar el modelo Silero VAD
requerido por la ruta de producción.

Si `dumpbin.exe` no está disponible, registra el warning. No instales MSVC ni
modifiques el sistema.

Si cualquiera de estas comprobaciones falla, reporta el defecto y DETENTE. No
corrijas el repositorio salvo autorización explícita.

## 5. Iniciar build real y terminar el turno

No ejecutes `package_gui.ps1` directamente esperando su finalización.

```powershell
.\scripts\start_package_build.ps1
.\scripts\package_build_status.ps1
```

El starter debe devolver rápidamente PID, ruta de
`build\package-build\build-status.json` y ruta de
`build\package-build\build.log`.

Si el estado es `RUNNING`, reporta esas rutas y **termina el turno
inmediatamente**. No esperes, no hagas polling y no continúes.

El usuario puede consultar cuando quiera:

```powershell
.\scripts\package_build_status.ps1
```

Estados: `RUNNING`, `SUCCESS`, `FAILED` o `BUILD_STATE_UNKNOWN`.

## 6. Reanudar sólo después de confirmación del usuario

Cuando el usuario indique que el build terminó:

```powershell
.\scripts\package_build_status.ps1
```

Si es `FAILED`, inspecciona `build.log`, reporta la causa y DETENTE.
No apliques una corrección sin autorización explícita.

Si es `SUCCESS`, confirma `dist\package-manifest.json` y conserva ruta del
ejecutable, SHA-256, file count, total bytes y `package_smoke = true`.

El package smoke habrá usado un MP4 temporal creado fuera del ejecutable y habrá
validado `tiny/cpu/int8` con TXT/JSON/SRT/VTT.

## 7. Ejecutable empaquetado

Lanza el `LocalCallTranscriber.exe` indicado por el manifest y comprueba que
abre la GUI, permanece responsiva, no muestra una consola normal y cierra
correctamente.

## 8. CLI después del empaquetado

```powershell
.\.venv\Scripts\local-call-transcriber.exe --help
.\.venv\Scripts\python.exe -m local_call_transcriber --help
```

## 9. Integridad del repositorio

```powershell
git status --short
git tag --list v0.2.0
```

`dist/`, `build/` y los artefactos Nuitka deben permanecer ignorados. El tag
debe seguir ausente.

## Reporte esperado de Codex

En el primer turno reporta sólo hasta el inicio del build desacoplado. En un
turno posterior, después de confirmación del usuario, completa:

- commit exacto;
- clone limpio;
- bootstrap;
- número de tests;
- Ruff/pip check;
- dry-run/preflight;
- PID/rutas de estado y log;
- `powershell_edition` y `powershell_version` registrados por el worker;
- estado final del build;
- package smoke;
- manifest;
- lanzamiento GUI;
- CLI;
- auditoría de datos/secretos;
- limitaciones.

No marques la Fase 12 como DONE, no crees el tag y no modifiques el repositorio
sin autorización explícita.
