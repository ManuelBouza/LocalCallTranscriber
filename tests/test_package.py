"""Pruebas ligeras del paquete, sin modelos ni GPU."""

import sys

import local_call_transcriber


def test_runtime_uses_validated_python_baseline() -> None:
    assert sys.version_info[:2] == (3, 11)


def test_package_is_importable() -> None:
    assert local_call_transcriber.__doc__
