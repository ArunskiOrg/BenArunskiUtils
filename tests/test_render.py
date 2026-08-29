import sys

import bootstrap
import pytest
import render


def test_find_edge_tts_returns_path_when_installed(monkeypatch):
    # Given edge-tts is on PATH
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/edge-tts")

    # When resolving the executable
    path = render.find_edge_tts()

    # Then it returns the resolved path without exiting
    assert path == "/usr/bin/edge-tts"


def test_find_edge_tts_exits_with_install_help_when_missing(monkeypatch):
    # Given edge-tts is not on PATH
    monkeypatch.setattr(render.shutil, "which", lambda name: None)

    # When resolving the executable
    # Then it exits with install instructions rather than failing later at subprocess time
    with pytest.raises(SystemExit, match="edge-tts was not found"):
        render.find_edge_tts()


def test_install_help_pins_the_minimum_version_bootstrap_declares():
    # Given the install help shown when the CLI is missing
    # When a user reads it
    # Then every install command pins the same minimum bootstrap declares, and it names the
    # command that confirms the installed version
    assert render.MIN_EDGE_TTS == bootstrap.MIN_EDGE_TTS
    assert render.INSTALL_HELP.count(f'"edge-tts>={render.MIN_EDGE_TTS}"') == 3
    assert "edge-tts --version" in render.INSTALL_HELP


def test_main_builds_edge_tts_command_with_defaults(tmp_path, monkeypatch):
    # Given a speech-ready input file and edge-tts available on PATH
    input_file = tmp_path / "doc.txt"
    input_file.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/edge-tts")

    captured_cmd = {}

    def fake_run(cmd, check):
        captured_cmd["cmd"] = cmd

    monkeypatch.setattr(render.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["render.py", str(input_file)])

    # When rendering with no explicit output/voice/rate
    render.main()

    # Then it defaults the output to <input>.mp3 and uses the documented default voice and rate
    cmd = captured_cmd["cmd"]
    assert cmd[0] == "/usr/bin/edge-tts"
    assert str(input_file.with_suffix(".mp3")) in cmd
    assert render.DEFAULT_VOICE in cmd
    assert f"--rate={render.DEFAULT_RATE}" in cmd


def test_main_exits_when_input_file_missing(tmp_path, monkeypatch):
    # Given an input path that does not exist
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/edge-tts")
    monkeypatch.setattr(sys, "argv", ["render.py", str(tmp_path / "missing.txt")])

    # When rendering
    # Then it exits with a clear message instead of letting edge-tts fail on a bad path
    with pytest.raises(SystemExit, match="not found"):
        render.main()


def test_default_engine_returns_edge_tts_when_no_marker(tmp_path, monkeypatch):
    # Given resources/bootstrap.py has never recorded a verified engine
    monkeypatch.setattr(render, "MARKER_PATH", tmp_path / ".bootstrap-verified")

    # When resolving the default engine
    # Then it falls back to edge-tts, the engine this repo is built around
    assert render.default_engine() == "edge-tts"


def test_default_engine_reads_the_bootstrap_marker(tmp_path, monkeypatch):
    # Given bootstrap.py has recorded a different verified engine
    marker = tmp_path / ".bootstrap-verified"
    marker.write_text("elevenlabs", encoding="utf-8")
    monkeypatch.setattr(render, "MARKER_PATH", marker)

    # When resolving the default engine
    # Then it reads back what bootstrap recorded
    assert render.default_engine() == "elevenlabs"


def test_main_rejects_an_engine_that_isnt_wired_up(tmp_path, monkeypatch):
    # Given a source file and an engine bootstrap.py knows about but render.py doesn't render with
    input_file = tmp_path / "doc.txt"
    input_file.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["render.py", str(input_file), "--engine", "elevenlabs"])

    # When rendering
    # Then it exits with a clear message pointing at the gap, instead of silently using edge-tts
    with pytest.raises(SystemExit, match="isn't wired into render.py yet"):
        render.main()


def test_main_prints_manual_command_when_edge_tts_call_fails(tmp_path, monkeypatch):
    # Given edge-tts is installed but the subprocess call itself fails (e.g. a sandboxed
    # shell blocking the network call edge-tts makes)
    import subprocess

    input_file = tmp_path / "doc.txt"
    input_file.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/edge-tts")

    def fake_run(cmd, check):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(render.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["render.py", str(input_file)])

    # When rendering
    # Then it exits with the equivalent command to run manually, not a raw traceback
    with pytest.raises(SystemExit, match="Run the command yourself"):
        render.main()
