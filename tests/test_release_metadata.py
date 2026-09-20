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
    assert "nuitka==2.6.8" in config["python"]["packages"]
    assert config["nuitka"]["mode"] == "standalone"

    extra_args = config["nuitka"]["extra_args"]
    assert "--windows-console-mode=disable" in extra_args
    assert "--include-package=local_call_transcriber" in extra_args
    assert "--include-package=faster_whisper" in extra_args
    assert "--include-package=ctranslate2" in extra_args


def test_packaged_entrypoint_keeps_release_smoke_available() -> None:
    entrypoint = (ROOT / "deploy" / "gui_main.py").read_text(encoding="utf-8")
    package_script = (ROOT / "scripts" / "package_gui.ps1").read_text(encoding="utf-8")

    assert '"--package-smoke"' in entrypoint
    assert "'--package-smoke'" in package_script
    assert 'model="tiny"' in entrypoint
    assert 'device="cpu"' in entrypoint
    assert 'compute_type="int8"' in entrypoint
