"""Basic smoke tests that do not require a running Ollama server."""

import os

import main


def test_translation_keys():
    assert main.T("exit") in ("exit", "salir")
    assert main.STRINGS["en"]["ready"] == "ready"


def test_get_base_dir_linux_uses_config():
    os.environ.pop("XDG_CONFIG_HOME", None)
    path = main.get_base_dir()
    assert path.endswith("ollama-run")
    assert ".config" in path or "ollama-run" in path


def test_is_vision_model():
    assert main.is_vision_model("llava:7b") is True
    assert main.is_vision_model("qwen2.5:7b") is False
    assert main.is_vision_model("") is False


def test_build_tag_format():
    assert main._BUILD_TAG.startswith("rnbw-ollama-")
