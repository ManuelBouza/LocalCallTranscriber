"""Pruebas ligeras del paquete, sin modelos ni GPU."""

import local_call_transcriber


def test_package_is_importable() -> None:
    assert local_call_transcriber.__doc__
