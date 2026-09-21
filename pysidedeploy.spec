[app]
title = LocalCallTranscriber
project_dir = .
input_file = deploy/gui_main.py
project_file =
exec_directory = dist
icon =

[python]
python_path = .venv/Scripts/python.exe
packages = nuitka==4.2.1,ordered_set,zstandard

[qt]
qml_files =
excluded_qml_plugins =
modules = Core,Gui,Widgets
plugins = platforms

[nuitka]
mode = standalone
extra_args = --quiet --assume-yes-for-downloads --noinclude-qt-translations --windows-console-mode=disable --include-package=local_call_transcriber --include-package=faster_whisper --include-package=ctranslate2 --include-module=huggingface_hub.utils._headers --include-module=huggingface_hub.utils._fixes --include-module=huggingface_hub.utils._validators --include-module=huggingface_hub.utils.logging
