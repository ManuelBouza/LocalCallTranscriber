"""Pruebas ligeras de metadatos y configuración del release v0.2.0."""

import configparser
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_version_is_0_2_0() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["version"] == "0.2.0"
    assert project["project"]["scripts"]["local-call-transcriber"]
    assert project["project"]["gui-scripts"]["local-call-transcriber-gui"]


def test_pyside_deploy_is_reproducible_standalone() -> None:
    config = configparser.ConfigParser()
    config.read(ROOT / "pysidedeploy.spec", encoding="utf-8")

    assert config["app"]["title"] == "LocalCallTranscriber"
    assert config["app"]["input_file"] == "deploy/gui_main.py"
    assert config["python"]["python_path"] == ".venv/Scripts/python.exe"
    assert "nuitka==4.2.1" in config["python"]["packages"]
    assert config["nuitka"]["mode"] == "standalone"

    extra_args = config["nuitka"]["extra_args"]
    assert "--assume-yes-for-downloads" in extra_args
    assert "--disable-cache=ccache" not in extra_args
    assert "--noinclude-qt-translations" in extra_args
    assert "--windows-console-mode=disable" in extra_args
    assert "--include-package=local_call_transcriber" in extra_args
    assert "--include-package=numpy" not in extra_args
    assert "--include-module=av." not in extra_args
    assert "--include-package=faster_whisper" in extra_args
    assert "--include-package=ctranslate2" in extra_args
    assert "--include-package=huggingface_hub.utils" in extra_args
    assert "--include-package=huggingface_hub " not in extra_args
    assert "--include-module=huggingface_hub.utils." not in extra_args


def test_packaged_entrypoint_uses_external_smoke_fixture() -> None:
    entrypoint = (ROOT / "deploy" / "gui_main.py").read_text(encoding="utf-8")
    fixture = (ROOT / "deploy" / "create_package_smoke_fixture.py").read_text(
        encoding="utf-8"
    )
    package_script = (ROOT / "scripts" / "package_gui.ps1").read_text(encoding="utf-8")

    assert '"--package-smoke"' in entrypoint
    assert "LOCALCALLTRANSCRIBER_PACKAGE_SMOKE_INPUT" in entrypoint
    assert "import numpy" not in entrypoint
    assert "import av" not in entrypoint
    assert "import numpy as np" in fixture
    assert "import av" in fixture
    assert "create_package_smoke_fixture.py" in package_script
    assert "Start-Process" in package_script
    assert "-FilePath $executable.FullName" in package_script
    assert "-ArgumentList '--package-smoke'" in package_script
    assert "-Wait" in package_script
    assert "-PassThru" in package_script
    assert "-RedirectStandardOutput $smokeStdout" in package_script
    assert "-RedirectStandardError $smokeStderr" in package_script
    assert 'model="tiny"' in entrypoint
    assert 'device="cpu"' in entrypoint
    assert 'compute_type="int8"' in entrypoint


def test_packaging_restores_spec_and_prepares_supported_mingw_include() -> None:
    package_script = (ROOT / "scripts" / "package_gui.ps1").read_text(encoding="utf-8")

    assert "ReadAllBytes($specFile)" in package_script
    assert "WriteAllBytes($specFile, $originalSpecBytes)" in package_script
    assert "getCachedDownloadedMinGW64" in package_script
    assert "nuitka==4.2.1" in package_script
    assert "x86_64-w64-mingw32\\include" in package_script
    assert "psdk_inc\\intrin-impl.h" in package_script
    assert "$originalCIncludePath = $env:C_INCLUDE_PATH" in package_script
    assert "$env:C_INCLUDE_PATH = $originalCIncludePath" in package_script
    assert "gui_main.exe" in package_script
    assert "Rename-Item" in package_script


def test_detached_package_build_has_observable_state() -> None:
    starter = (ROOT / "scripts" / "start_package_build.ps1").read_text(encoding="utf-8")
    worker = (ROOT / "scripts" / "package_build_worker.ps1").read_text(encoding="utf-8")
    status = (ROOT / "scripts" / "package_build_status.ps1").read_text(encoding="utf-8")

    assert "Start-Process" in starter
    assert "-PassThru" in starter
    assert "-Wait" not in starter
    assert "build-status.json" in starter
    assert "build.log" in starter
    assert "'RUNNING'" in worker
    assert "'SUCCESS'" in worker
    assert "'FAILED'" in worker
    assert "exit_code" in worker
    assert "BUILD_PROCESS_RUNNING" in status
    assert "BUILD_SUCCESS" in status
    assert "BUILD_FAILED" in status
    assert "BUILD_STATE_UNKNOWN" in status
    assert "pwsh.exe" in starter
    assert "powershell.exe" in starter
    assert "powershell_edition" in worker
    assert "powershell_version" in worker
    assert "PS edition:" in status
    assert "PS version:" in status

    package_script = (ROOT / "scripts" / "package_gui.ps1").read_text(encoding="utf-8")
    assert "Invoke-NativeCaptured" in package_script
    assert "$ErrorActionPreference = 'Continue'" in package_script
    assert "from importlib.metadata import version" in package_script
