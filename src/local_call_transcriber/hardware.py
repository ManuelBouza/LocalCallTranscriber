"""Selección de hardware y preparación local del runtime CUDA en Windows."""

import os
from pathlib import Path

DEVICE_CHOICES = ("auto", "cpu", "cuda")
COMPUTE_TYPE_CHOICES = ("auto", "int8", "float16", "int8_float16")
_DLL_DIRECTORY_HANDLES: list[object] = []


def prepare_cuda_runtime() -> None:
    """Añade cuDNN instalado por usuario al proceso actual, si está disponible.

    No altera variables globales ni hace que CUDA sea obligatorio: sólo permite que
    CTranslate2 encuentre las DLL cuando se solicita una ruta CUDA.
    """
    if not hasattr(os, "add_dll_directory"):
        return

    directories: list[Path] = []
    cuda_path = os.environ.get(
        "CUDA_PATH", r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6"
    )
    directories.append(Path(cuda_path) / "bin")

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        directories.append(Path(local_app_data) / "NVIDIA" / "CUDNN" / "v9.11" / "bin")

    for directory in directories:
        if directory.is_dir():
            directory_text = str(directory)
            path_entries = os.environ.get("PATH", "").split(os.pathsep)
            if directory_text not in path_entries:
                os.environ["PATH"] = directory_text + os.pathsep + os.environ.get("PATH", "")
            _DLL_DIRECTORY_HANDLES.append(os.add_dll_directory(directory_text))
