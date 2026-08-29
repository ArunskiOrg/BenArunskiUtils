import bootstrap
import pytest


def test_check_python_true_when_version_meets_floor(monkeypatch):
    # Given the interpreter meets the documented Python floor
    monkeypatch.setattr(bootstrap.sys, "version_info", (3, 9, 0))

    # When checking Python
    # Then it passes
    assert bootstrap.check_python() is True


def test_check_python_false_when_version_below_floor(monkeypatch):
    # Given the interpreter is older than the documented floor
    monkeypatch.setattr(bootstrap.sys, "version_info", (3, 8, 5))

    # When checking Python
    # Then it fails
    assert bootstrap.check_python() is False


def test_edge_tts_available_when_on_path(monkeypatch):
    # Given edge-tts is on PATH
    monkeypatch.setattr(
        bootstrap.shutil, "which", lambda name: "/usr/bin/edge-tts" if name == "edge-tts" else None
    )

    # When checking the engine registry
    status = {s["id"]: s for s in bootstrap.engine_status("Linux")}

    # Then edge-tts reports available, with the pip-style install commands present regardless
    assert status["edge-tts"]["available"] is True
    assert status["edge-tts"]["install"] == bootstrap.PIP_STYLE_INSTALL


def test_edge_tts_unavailable_reports_install_commands(monkeypatch):
    # Given edge-tts is not on PATH
    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: None)

    # When checking the engine registry
    status = {s["id"]: s for s in bootstrap.engine_status("Windows")}

    # Then it's marked unavailable but still offers the install commands
    assert status["edge-tts"]["available"] is False
    assert "uv" in status["edge-tts"]["install"]


def test_edge_tts_install_commands_pin_the_minimum_version():
    # Given the registry's pip-style install commands
    # When each is read
    # Then every one pins the minimum version the skill is documented against
    assert all(
        f'edge-tts>={bootstrap.MIN_EDGE_TTS}' in command
        for command in bootstrap.PIP_STYLE_INSTALL.values()
    )


def test_edge_tts_note_states_the_minimum_version():
    # Given the edge-tts registry entry
    note = bootstrap.ENGINES["edge-tts"]["note"]

    # When a user reads the note bootstrap prints
    # Then it names the minimum version and how to confirm the installed one
    assert bootstrap.MIN_EDGE_TTS in note
    assert "edge-tts --version" in note


@pytest.mark.parametrize(
    "os_name, which_result, expect_available",
    [
        pytest.param("Darwin", "/usr/bin/say", True, id="darwin_with_say_on_path"),
        pytest.param("Darwin", None, False, id="darwin_without_say_on_path"),
        pytest.param("Windows", "/usr/bin/say", False, id="non_darwin_even_if_something_named_say_exists"),
    ],
)
def test_macos_say_availability(monkeypatch, os_name, which_result, expect_available):
    # Given a platform and whether a "say" binary is on PATH
    monkeypatch.setattr(bootstrap.platform, "system", lambda: os_name)
    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: which_result if name == "say" else None)

    # When checking the engine registry
    status = {s["id"]: s for s in bootstrap.engine_status(os_name)}

    # Then availability requires both being on Darwin and having the binary
    assert status["macos-say"]["available"] is expect_available


def test_macos_say_install_note_only_offered_on_darwin():
    # Given a non-Darwin OS
    # When checking the engine registry
    status = {s["id"]: s for s in bootstrap.engine_status("Linux")}

    # Then there's no install suggestion, since say only ships with macOS
    assert status["macos-say"]["install"] is None


def test_api_key_engine_available_when_env_var_set(monkeypatch):
    # Given the ElevenLabs API key is set in the environment
    monkeypatch.setenv("ELEVENLABS_API_KEY", "secret")

    # When checking the engine registry
    status = {s["id"]: s for s in bootstrap.engine_status("Linux")}

    # Then it reports available, with no install command (it's a sign-up, not an install)
    assert status["elevenlabs"]["available"] is True
    assert status["elevenlabs"]["install"] is None


def test_api_key_engine_unavailable_when_env_var_missing(monkeypatch):
    # Given the ElevenLabs API key is not set
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)

    # When checking the engine registry
    status = {s["id"]: s for s in bootstrap.engine_status("Linux")}

    # Then it reports unavailable
    assert status["elevenlabs"]["available"] is False


def test_cmd_check_exits_zero_message_when_available(monkeypatch, capsys):
    # Given an available engine
    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: "/usr/bin/edge-tts")

    # When checking it by id
    bootstrap.cmd_check("edge-tts")

    # Then it prints a plain confirmation and does not exit the process
    assert "available" in capsys.readouterr().out


def test_cmd_check_exits_with_install_commands_when_unavailable(monkeypatch):
    # Given edge-tts is not available
    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: None)

    # When checking it by id
    # Then it exits with the install commands, version-pinned, not a bare failure
    with pytest.raises(SystemExit, match=f'uv tool install "edge-tts>={bootstrap.MIN_EDGE_TTS}"'):
        bootstrap.cmd_check("edge-tts")


def test_cmd_check_exits_clearly_on_unknown_engine():
    # Given an id that isn't in the registry
    # When checking it
    # Then it exits with a message pointing at --list, not a KeyError
    with pytest.raises(SystemExit, match="Unknown engine"):
        bootstrap.cmd_check("not-a-real-engine")


def test_mark_verified_then_verified_round_trips(tmp_path, monkeypatch, capsys):
    # Given a fresh marker location
    monkeypatch.setattr(bootstrap, "MARKER_PATH", tmp_path / ".bootstrap-verified")

    # When an engine is marked verified
    bootstrap.cmd_mark_verified("edge-tts")

    # Then --verified reports it back
    bootstrap.cmd_verified()
    assert capsys.readouterr().out.strip().endswith("edge-tts")


def test_verified_exits_nonzero_when_nothing_recorded(tmp_path, monkeypatch):
    # Given no marker has ever been written
    monkeypatch.setattr(bootstrap, "MARKER_PATH", tmp_path / ".bootstrap-verified")

    # When checking what's verified
    # Then it exits non-zero rather than printing nothing ambiguously
    with pytest.raises(SystemExit):
        bootstrap.cmd_verified()


def test_reset_clears_a_previously_written_marker(tmp_path, monkeypatch):
    # Given a marker was previously recorded
    marker = tmp_path / ".bootstrap-verified"
    marker.write_text("edge-tts", encoding="utf-8")
    monkeypatch.setattr(bootstrap, "MARKER_PATH", marker)

    # When resetting
    bootstrap.cmd_reset()

    # Then the marker file is gone
    assert not marker.exists()


def test_reset_is_a_no_op_when_nothing_was_recorded(tmp_path, monkeypatch):
    # Given no marker file exists
    monkeypatch.setattr(bootstrap, "MARKER_PATH", tmp_path / ".bootstrap-verified")

    # When resetting
    # Then it does not raise
    bootstrap.cmd_reset()
