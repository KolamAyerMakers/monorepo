"""Tests for learner registration CLI argument parsing."""

from __future__ import annotations

from maker_guide.registration.cli import parse_arguments


def test_parse_arguments_reads_custom_commands() -> None:
    """Registration command paths can be overridden by deployment wiring."""
    options = parse_arguments(
        [
            "--create-user-command",
            "/opt/maker-guide-test/bin/create-user",
            "--sudo-command",
            "/opt/maker-guide-test/bin/sudo",
            "--getent-command",
            "/opt/maker-guide-test/bin/getent",
            "--pwscore-command",
            "/opt/maker-guide-test/bin/pwscore",
            "--logo-command",
            "/opt/maker-guide-test/bin/logo",
            "--fully-qualified-domain-name",
            "classroom.example",
            "--login-host",
            "login.example",
            "--web-ssh-url",
            "https://ssh.example",
        ],
    )

    assert options.create_user_command == "/opt/maker-guide-test/bin/create-user"
    assert options.sudo_command == "/opt/maker-guide-test/bin/sudo"
    assert options.getent_command == "/opt/maker-guide-test/bin/getent"
    assert options.pwscore_command == "/opt/maker-guide-test/bin/pwscore"
    assert options.logo_command == "/opt/maker-guide-test/bin/logo"
    assert options.fully_qualified_domain_name == "classroom.example"
    assert options.login_host == "login.example"
    assert options.web_ssh_url == "https://ssh.example"
