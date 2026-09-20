[app]
title = LocalCallTranscriber
project_dir = .
input_file = deploy/gui_main.py
project_file =
exec_directory = dist
icon =

[python]
python_path = .venv/Scripts/python.exe
packages = nuitka==2.6.8,ordered_set,zstandard

[qt]
qml_files =
excluded_qml_plugins =
modules = Core,Gui,Widgets
plugins = platforms

[nuitka]
mode = standalone
extra_args = --quiet --assume-yes-for-downloads --disable-cache=ccache --noinclude-qt-translations --windows-console-mode=disable --include-package=local_call_transcriber --include-module=av.utils --include-package=faster_whisper --include-package=ctranslate2
