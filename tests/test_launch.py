"""Pure unit tests for launch configuration helpers."""

from __future__ import annotations

from mcp_caretaker.launch import LaunchSpec, build_child_env, redact_values


def test_env_builder_drops_parent_variables(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CARETAKER_PARENT_ONLY_FAKE", "FAKE-PARENT-VALUE-NOT-A-SECRET")
    spec = LaunchSpec(argv=("python", "-V"))
    env = build_child_env(spec, tmp_path)
    assert "CARETAKER_PARENT_ONLY_FAKE" not in env
    assert "HOME" not in env
    assert "USERPROFILE" not in env
    assert env["TEMP"] == str(tmp_path)
    assert env["TMP"] == str(tmp_path)


def test_env_builder_adds_extra_env(tmp_path) -> None:
    spec = LaunchSpec(
        argv=("python", "-V"),
        extra_env={"CARETAKER_FAKE_SECRET": "FAKE-VALUE-1234", "TEMP": "OVERRIDE"},
    )
    env = build_child_env(spec, tmp_path)
    assert env["CARETAKER_FAKE_SECRET"] == "FAKE-VALUE-1234"
    assert env["TEMP"] == "OVERRIDE"


def test_spec_repr_never_contains_env_values() -> None:
    secret = "FAKE-SECRET-VALUE-987654"
    spec = LaunchSpec(
        argv=("python", "server.py"),
        extra_env={"CARETAKER_FAKE_SECRET": secret, "SHORT": "x"},
    )
    assert secret not in repr(spec)
    assert secret not in str(spec)
    assert "CARETAKER_FAKE_SECRET" in repr(spec)
    assert "SHORT" in repr(spec)


def test_redact_values_replaces_values_and_keeps_names() -> None:
    extra = {"LONG_NAME": "FAKE-LONG-VALUE-1234", "SHORT": "abc"}
    text = "before FAKE-LONG-VALUE-1234 after abc"
    assert redact_values(text, extra) == "before [REDACTED:LONG_NAME] after abc"
    # Longer values are replaced first, so a shorter secret cannot half-redact one.
    assert redact_values("abcdef", {"A": "abcdef", "B": "abc"}) == "[REDACTED:A]"
