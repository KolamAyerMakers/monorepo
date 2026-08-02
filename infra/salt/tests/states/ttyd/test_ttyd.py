"""Tests for ttyd state."""

from __future__ import annotations

import importlib
import os
import subprocess
import textwrap
from collections.abc import MutableMapping
from pathlib import Path
from typing import Protocol, TypeGuard, cast

import pytest

from tests.support.paths import SALTSTACK_DIRECTORY


class _Template(Protocol):
    def render(self, **context: object) -> str:
        """Render template."""
        ...


class _Environment(Protocol):
    filters: MutableMapping[str, "_YamlFilter"]

    def get_template(self, name: str) -> _Template:
        """Return template."""
        ...


class _EnvironmentFactory(Protocol):
    def __call__(
        self,
        *,
        loader: object,
        trim_blocks: bool,
        lstrip_blocks: bool,
    ) -> _Environment: ...


class _LoaderFactory(Protocol):
    def __call__(self, searchpath: str) -> object: ...


class _YamlFilter(Protocol):
    def __call__(self, value: object) -> str:
        """Render a value as YAML."""
        ...


class _YamlModule(Protocol):
    def safe_load(self, value: str) -> object:
        """Load YAML."""
        ...

    def safe_dump(self, value: object, *, default_flow_style: bool) -> str:
        """Dump YAML."""
        ...


def _is_string_object_dictionary(value: object) -> TypeGuard[dict[str, object]]:
    if not isinstance(value, dict):
        return False
    dictionary = cast(dict[object, object], value)
    return all(isinstance(key, str) for key in dictionary)


class _SaltNamespace:
    def __init__(self, pillar: dict[str, object] | None = None) -> None:
        self._pillar: dict[str, object] = pillar or {}

    def __getitem__(self, key: str) -> object:
        if key == "pillar.get":
            return self.pillar_get
        raise KeyError(key)

    def pillar_get(self, key: str, default: object = None) -> object:
        """Return pillar data for the requested key."""
        value: object = self._pillar
        for component in key.split(":"):
            if not _is_string_object_dictionary(value) or component not in value:
                return default
            value = value[component]
        return value


def _yaml_filter(value: object) -> str:
    yaml_module = cast(_YamlModule, cast(object, importlib.import_module("yaml")))
    return (
        yaml_module.safe_dump(value, default_flow_style=True)
        .strip()
        .removesuffix("\n...")
    )


def _load_state(
    template: str, pillar: dict[str, object] | None = None
) -> dict[str, object]:
    jinja2 = importlib.import_module("jinja2")
    environment_factory = cast(_EnvironmentFactory, getattr(jinja2, "Environment"))
    loader_factory = cast(_LoaderFactory, getattr(jinja2, "FileSystemLoader"))
    environment = environment_factory(
        loader=loader_factory(str(SALTSTACK_DIRECTORY / "states")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["yaml"] = _yaml_filter
    yaml_module = cast(_YamlModule, cast(object, importlib.import_module("yaml")))
    return cast(
        dict[str, object],
        yaml_module.safe_load(
            environment.get_template(template).render(salt=_SaltNamespace(pillar))
        ),
    )


def _render_template(template: str, context: dict[str, object]) -> str:
    jinja2 = importlib.import_module("jinja2")
    environment_factory = cast(_EnvironmentFactory, getattr(jinja2, "Environment"))
    loader_factory = cast(_LoaderFactory, getattr(jinja2, "FileSystemLoader"))
    environment = environment_factory(
        loader=loader_factory(str(SALTSTACK_DIRECTORY / "states")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["yaml"] = _yaml_filter
    return environment.get_template(template).render(**context)


def test_ssh_sso_allows_linux_foundations_members_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Web SSH recovery accepts only Linux Foundations course members."""
    command_directory = tmp_path / "bin"
    command_directory.mkdir()
    for command_name, command_body in {
        "getent": "exit 0\n",
        "id": "printf '%s\\n' \"$TTYD_GROUPS\"\n",
    }.items():
        command_path = command_directory / command_name
        _ = command_path.write_text(f"#!/bin/sh\n{command_body}", encoding="utf-8")
        _ = command_path.chmod(0o755)

    monkeypatch.setenv("PATH", f"{command_directory}{os.pathsep}{os.environ['PATH']}")
    rendered = _render_template(
        "roles/kam-classroom/templates/ttyd_ssh_sso.sh.j2",
        {"web_ssh_url": "https://classroom.example/ssh/"},
    )

    for group_names, expected_denial_message in (
        ("linux-foundations", ""),
        ("legacy-course", "Web SSH recovery is available only to Linux Foundations"),
    ):
        result = subprocess.run(
            ["/bin/sh", "-c", rendered],
            capture_output=True,
            check=False,
            env={**os.environ, "TTYD_USER": "nobody", "TTYD_GROUPS": group_names},
            text=True,
        )

        assert result.returncode != 0
        if expected_denial_message:
            assert expected_denial_message in result.stderr
        else:
            assert (
                "Web SSH recovery is available only to Linux Foundations"
                not in result.stderr
            )


def _pillar() -> dict[str, object]:
    return {
        "ttyd": {
            "service": {
                "user": "ttyd",
                "group": "ttyd",
                "uid": 984,
                "gid": 978,
                "shell": "/usr/sbin/nologin",
                "home": "/var/lib/ttyd",
                "system_user": True,
                "create_home": False,
                "unit_directory": "/etc/systemd/system",
                "protect_clock": True,
                "protect_kernel_logs": True,
                "restrict_realtime": True,
                "system_call_architectures": "native",
            },
            "web": {
                "assets": {
                    "route": "/ttyd-assets",
                    "directory": "/var/lib/ttyd/assets",
                    "favicon": {
                        "name": "terminal.svg",
                        "source": "salt://ttyd/files/terminal.svg",
                    },
                    "fonts": [
                        {
                            "name": "HackNerdFontMono-Regular.ttf",
                            "url": "https://github.com/ryanoasis/nerd-fonts/raw/v3.4.0/patched-fonts/Hack/Regular/HackNerdFontMono-Regular.ttf",
                            "checksum": "sha256=03e60d3c1a9f8bef4e1f78836f80aacb9ec005260a6b094f5bfc10043bb115ab",
                            "family": "HackNerdFontMono",
                            "weight": 400,
                            "style": "normal",
                            "format": "truetype",
                        }
                    ],
                },
                "custom_index": {
                    "path": "/var/lib/ttyd/index.html",
                    "builder": "/usr/local/sbin/ttyd-build-custom-index",
                    "stylesheet_path": "/ssh/ttyd-assets/ttyd-fonts.css",
                    "build_port": 17682,
                },
            },
            "instances": {
                "registration": {
                    "server": {
                        "domain": "lf2607.kolamayermakers.org",
                        "host": "127.0.0.1",
                        "port": 7681,
                    },
                    "command": (
                        "/usr/bin/ssh -tt -o PreferredAuthentications=none "
                        "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
                        "-o LogLevel=ERROR new@localhost"
                    ),
                },
                "ssh": {
                    "run_user": "root",
                    "run_group": "root",
                    "auth_header": "X-WEBAUTH-USER",
                    "private_tmp": False,
                    "protect_home": False,
                    "read_write_paths": ["/var/lib/ttyd", "/home", "/tmp"],
                    "server": {
                        "domain": "lf2607.kolamayermakers.org",
                        "url": "https://lf2607.kolamayermakers.org/ssh/",
                        "socket": "/run/ttyd-ssh/ssh.sock",
                        "socket_owner": "caddy:caddy",
                        "upstream": "unix//run/ttyd-ssh/ssh.sock",
                    },
                    "index": "/var/lib/ttyd/index.html",
                    "client_options": ["fontFamily=HackNerdFontMono,monospace"],
                    "command": "/usr/local/sbin/ttyd-ssh-sso",
                },
            },
        }
    }


def test_ttyd_instance_unit_grants_capabilities_only_to_root_instances() -> None:
    """Test ttyd systemd unit capabilities for normal and SSO instances."""
    service = {
        "user": "ttyd",
        "group": "ttyd",
        "home": "/var/lib/ttyd",
        "protect_clock": True,
        "protect_kernel_logs": True,
        "restrict_realtime": True,
        "system_call_architectures": "native",
    }

    assert _render_template(
        "ttyd/templates/ttyd-instance.service.j2",
        {
            "instance_name": "registration",
            "service": service,
            "server": {"host": "127.0.0.1", "port": 7681},
            "command": "/usr/bin/ssh new@localhost",
            "run_user": "ttyd",
            "run_group": "ttyd",
            "auth_header": "",
            "private_tmp": True,
            "protect_home": True,
            "read_write_paths": ["/var/lib/ttyd"],
            "index": "",
            "client_options": [],
        },
    ) == textwrap.dedent(
        """\
        [Unit]
        Description=ttyd web terminal (registration)
        Documentation=https://github.com/tsl0922/ttyd
        After=network-online.target ssh.service
        Wants=network-online.target

        [Service]
        Type=simple
        User=ttyd
        Group=ttyd
        WorkingDirectory=/var/lib/ttyd
        Environment=HOME=/var/lib/ttyd
        ExecStart=/usr/local/bin/ttyd --interface 127.0.0.1 --port 7681 --writable /usr/bin/ssh new@localhost
        Restart=on-failure
        RestartSec=5s
        RuntimeDirectory=ttyd-registration
        RuntimeDirectoryMode=0755
        UMask=0027
        NoNewPrivileges=true
        PrivateTmp=true
        ProtectHome=true
        ProtectSystem=strict
        ReadWritePaths=/var/lib/ttyd
        ProtectKernelTunables=true
        ProtectKernelModules=true
        ProtectControlGroups=true
        ProtectClock=true
        ProtectKernelLogs=true
        RestrictNamespaces=true
        RestrictSUIDSGID=true
        RestrictRealtime=true
        LockPersonality=true
        SystemCallArchitectures=native
        CapabilityBoundingSet=
        AmbientCapabilities=

        [Install]
        WantedBy=multi-user.target
        """
    ).removesuffix("\n")

    assert _render_template(
        "ttyd/templates/ttyd-instance.service.j2",
        {
            "instance_name": "ssh",
            "service": service,
            "server": {
                "socket": "/run/ttyd-ssh/ssh.sock",
                "socket_owner": "caddy:caddy",
            },
            "command": "/usr/local/sbin/ttyd-ssh-sso",
            "run_user": "root",
            "run_group": "root",
            "auth_header": "X-WEBAUTH-USER",
            "private_tmp": False,
            "protect_home": False,
            "read_write_paths": ["/var/lib/ttyd", "/home", "/tmp"],
            "index": "/var/lib/ttyd/index.html",
            "client_options": ["fontFamily=HackNerdFontMono,monospace"],
        },
    ) == textwrap.dedent(
        """\
        [Unit]
        Description=ttyd web terminal (ssh)
        Documentation=https://github.com/tsl0922/ttyd
        After=network-online.target ssh.service
        Wants=network-online.target

        [Service]
        Type=simple
        User=root
        Group=root
        WorkingDirectory=/var/lib/ttyd
        Environment=HOME=/var/lib/ttyd
        ExecStart=/usr/local/bin/ttyd --interface /run/ttyd-ssh/ssh.sock --socket-owner caddy:caddy --index /var/lib/ttyd/index.html --auth-header X-WEBAUTH-USER --client-option "fontFamily=HackNerdFontMono,monospace" --writable /usr/local/sbin/ttyd-ssh-sso
        Restart=on-failure
        RestartSec=5s
        RuntimeDirectory=ttyd-ssh
        RuntimeDirectoryMode=0755
        UMask=0027
        NoNewPrivileges=true
        PrivateTmp=false
        ProtectHome=false
        ProtectSystem=strict
        ReadWritePaths=/var/lib/ttyd /home /tmp
        ProtectKernelTunables=true
        ProtectKernelModules=true
        ProtectControlGroups=true
        ProtectClock=true
        ProtectKernelLogs=true
        RestrictNamespaces=true
        RestrictSUIDSGID=true
        RestrictRealtime=true
        LockPersonality=true
        SystemCallArchitectures=native
        CapabilityBoundingSet=CAP_CHOWN CAP_FOWNER CAP_SETGID CAP_SETUID
        AmbientCapabilities=CAP_CHOWN CAP_FOWNER CAP_SETGID CAP_SETUID

        [Install]
        WantedBy=multi-user.target
        """
    ).removesuffix("\n")


def test_ttyd_package_installs_pinned_binary_package() -> None:
    """Test ttyd package state."""
    assert _load_state("ttyd/package.sls") == {
        "include": ["github.download_egress"],
        "ttyd": {
            "packages.binary_package": [
                {"name": "ttyd"},
                {
                    "require": [
                        {"test": "bootstrap::package_sources_ready"},
                        {"test": "github::download_egress::ready"},
                    ]
                },
            ]
        },
    }


def test_ttyd_web_fonts_stylesheet_renders_font_faces() -> None:
    """Test the web font stylesheet rendered for ttyd."""
    assert _render_template(
        "ttyd/templates/web-fonts.css.j2",
        {
            "asset_route": "/ttyd-assets",
            "fonts": [
                {
                    "name": "HackNerdFontMono-Regular.ttf",
                    "family": "HackNerdFontMono",
                    "weight": 400,
                    "style": "normal",
                    "format": "truetype",
                },
                {
                    "name": "HackNerdFontMono-Bold.ttf",
                    "family": "HackNerdFontMono",
                    "weight": 700,
                    "style": "normal",
                    "format": "truetype",
                },
            ],
        },
    ) == textwrap.dedent(
        """\
        @font-face {
            font-family: 'HackNerdFontMono';
            src: url('/ttyd-assets/fonts/HackNerdFontMono-Regular.ttf') format('truetype');
            font-weight: 400;
            font-style: normal;
            font-display: block;
        }

        @font-face {
            font-family: 'HackNerdFontMono';
            src: url('/ttyd-assets/fonts/HackNerdFontMono-Bold.ttf') format('truetype');
            font-weight: 700;
            font-style: normal;
            font-display: block;
        }

        .xterm,
        .xterm * {
            font-family: 'HackNerdFontMono', monospace !important;
        }
        """
    )


def test_ttyd_instances_runs_registration_ssh_command() -> None:
    """Test ttyd named instance low state."""
    assert _load_state("ttyd/instances.sls", _pillar()) == {
        "include": ["ttyd.package"],
        "ttyd::instances::required_pillar": {
            "test.check_pillar": [
                {
                    "string": [
                        "ttyd:service:user",
                        "ttyd:service:group",
                        "ttyd:service:shell",
                        "ttyd:service:home",
                        "ttyd:service:unit_directory",
                        "ttyd:service:system_call_architectures",
                    ]
                },
                {
                    "boolean": [
                        "ttyd:service:system_user",
                        "ttyd:service:create_home",
                        "ttyd:service:protect_clock",
                        "ttyd:service:protect_kernel_logs",
                        "ttyd:service:restrict_realtime",
                    ]
                },
                {"integer": ["ttyd:service:uid", "ttyd:service:gid"]},
                {"dictionary": ["ttyd:instances"]},
                {"failhard": True},
            ]
        },
        "ttyd::web::required_pillar": {
            "test.check_pillar": [
                {
                    "string": [
                        "ttyd:web:assets:route",
                        "ttyd:web:assets:directory",
                        "ttyd:web:assets:favicon:name",
                        "ttyd:web:assets:favicon:source",
                        "ttyd:web:custom_index:path",
                        "ttyd:web:custom_index:builder",
                        "ttyd:web:custom_index:stylesheet_path",
                        "ttyd:web:assets:fonts:0:name",
                        "ttyd:web:assets:fonts:0:url",
                        "ttyd:web:assets:fonts:0:checksum",
                        "ttyd:web:assets:fonts:0:family",
                        "ttyd:web:assets:fonts:0:style",
                        "ttyd:web:assets:fonts:0:format",
                    ]
                },
                {
                    "integer": [
                        "ttyd:web:custom_index:build_port",
                        "ttyd:web:assets:fonts:0:weight",
                    ]
                },
                {"listing": ["ttyd:web:assets:fonts"]},
                {"failhard": True},
            ]
        },
        "/var/lib/ttyd/assets": {
            "file.directory": [
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {"makedirs": True},
                {
                    "require": [
                        {"user": "ttyd::user"},
                        {"test": "ttyd::web::required_pillar"},
                    ]
                },
            ]
        },
        "/var/lib/ttyd/assets/fonts": {
            "file.directory": [
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {
                    "require": [
                        {"file": "/var/lib/ttyd/assets"},
                        {"test": "ttyd::web::required_pillar"},
                    ]
                },
            ]
        },
        "ttyd::web::favicon": {
            "file.managed": [
                {"name": "/var/lib/ttyd/assets/terminal.svg"},
                {"source": "salt://ttyd/files/terminal.svg"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {
                    "require": [
                        {"file": "/var/lib/ttyd/assets"},
                        {"test": "ttyd::web::required_pillar"},
                    ]
                },
            ]
        },
        "ttyd::web::font::HackNerdFontMono-Regular.ttf": {
            "file.managed": [
                {"name": "/var/lib/ttyd/assets/fonts/HackNerdFontMono-Regular.ttf"},
                {
                    "source": (
                        "https://github.com/ryanoasis/nerd-fonts/raw/v3.4.0/"
                        "patched-fonts/Hack/Regular/HackNerdFontMono-Regular.ttf"
                    )
                },
                {
                    "source_hash": (
                        "sha256=03e60d3c1a9f8bef4e1f78836f80aacb9ec005260a6b094f5bfc10043bb115ab"
                    )
                },
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {
                    "require": [
                        {"file": "/var/lib/ttyd/assets/fonts"},
                        {"test": "github::download_egress::ready"},
                        {"test": "ttyd::web::required_pillar"},
                    ]
                },
            ]
        },
        "/var/lib/ttyd/assets/ttyd-fonts.css": {
            "file.managed": [
                {"source": "salt://ttyd/templates/web-fonts.css.j2"},
                {"template": "jinja"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {
                    "context": {
                        "asset_route": "/ttyd-assets",
                        "fonts": [
                            {
                                "name": "HackNerdFontMono-Regular.ttf",
                                "url": (
                                    "https://github.com/ryanoasis/nerd-fonts/raw/v3.4.0/"
                                    "patched-fonts/Hack/Regular/"
                                    "HackNerdFontMono-Regular.ttf"
                                ),
                                "checksum": (
                                    "sha256=03e60d3c1a9f8bef4e1f78836f80aacb9ec005260a6b094f5bfc10043bb115ab"
                                ),
                                "family": "HackNerdFontMono",
                                "weight": 400,
                                "style": "normal",
                                "format": "truetype",
                            }
                        ],
                    }
                },
                {
                    "require": [
                        {"file": "/var/lib/ttyd/assets"},
                        {"file": "ttyd::web::font::HackNerdFontMono-Regular.ttf"},
                        {"test": "ttyd::web::required_pillar"},
                    ]
                },
            ]
        },
        "/usr/local/sbin/ttyd-build-custom-index": {
            "file.managed": [
                {"source": "salt://ttyd/files/ttyd_build_custom_index.py"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {"require": [{"test": "ttyd::web::required_pillar"}]},
            ]
        },
        "ttyd::web::custom_index::initial": {
            "cmd.run": [
                {
                    "name": (
                        "/usr/local/sbin/ttyd-build-custom-index "
                        "--output /var/lib/ttyd/index.html "
                        "--stylesheet /ssh/ttyd-assets/ttyd-fonts.css "
                        "--favicon /ttyd-assets/terminal.svg "
                        "--font-family HackNerdFontMono --port 17682"
                    )
                },
                {"creates": "/var/lib/ttyd/index.html"},
                {
                    "require": [
                        {"packages": "ttyd"},
                        {"file": "/usr/local/sbin/ttyd-build-custom-index"},
                        {"file": "ttyd::web::favicon"},
                        {"file": "/var/lib/ttyd/assets/ttyd-fonts.css"},
                        {"test": "ttyd::web::required_pillar"},
                    ]
                },
            ]
        },
        "ttyd::web::custom_index::updated": {
            "cmd.run": [
                {
                    "name": (
                        "/usr/local/sbin/ttyd-build-custom-index "
                        "--output /var/lib/ttyd/index.html "
                        "--stylesheet /ssh/ttyd-assets/ttyd-fonts.css "
                        "--favicon /ttyd-assets/terminal.svg "
                        "--font-family HackNerdFontMono --port 17682"
                    )
                },
                {
                    "onchanges": [
                        {"packages": "ttyd"},
                        {"file": "/usr/local/sbin/ttyd-build-custom-index"},
                        {"file": "ttyd::web::favicon"},
                        {"file": "/var/lib/ttyd/assets/ttyd-fonts.css"},
                    ]
                },
                {
                    "require": [
                        {"packages": "ttyd"},
                        {"file": "/usr/local/sbin/ttyd-build-custom-index"},
                        {"file": "ttyd::web::favicon"},
                        {"file": "/var/lib/ttyd/assets/ttyd-fonts.css"},
                        {"test": "ttyd::web::required_pillar"},
                    ]
                },
            ]
        },
        "ttyd::web::custom_index::file": {
            "file.managed": [
                {"name": "/var/lib/ttyd/index.html"},
                {"replace": False},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {
                    "require": [
                        {"cmd": "ttyd::web::custom_index::initial"},
                        {"cmd": "ttyd::web::custom_index::updated"},
                        {"test": "ttyd::web::required_pillar"},
                    ]
                },
            ]
        },
        "ttyd::group": {
            "group.present": [
                {"name": "ttyd"},
                {"system": True},
                {"gid": 978},
                {"require": [{"test": "ttyd::instances::required_pillar"}]},
            ]
        },
        "ttyd::user": {
            "user.present": [
                {"name": "ttyd"},
                {"system": True},
                {"uid": 984},
                {"shell": "/usr/sbin/nologin"},
                {"home": "/var/lib/ttyd"},
                {"createhome": False},
                {"gid": "ttyd"},
                {
                    "require": [
                        {"group": "ttyd::group"},
                        {"test": "ttyd::instances::required_pillar"},
                    ]
                },
            ]
        },
        "ttyd::home": {
            "file.directory": [
                {"name": "/var/lib/ttyd"},
                {"user": "ttyd"},
                {"group": "ttyd"},
                {"mode": "0755"},
                {"makedirs": True},
                {
                    "require": [
                        {"user": "ttyd::user"},
                        {"test": "ttyd::instances::required_pillar"},
                    ]
                },
            ]
        },
        "ttyd::instance::registration::required_pillar": {
            "test.check_pillar": [
                {
                    "string": [
                        "ttyd:instances:registration:command",
                        "ttyd:instances:registration:server:host",
                    ]
                },
                {"integer": ["ttyd:instances:registration:server:port"]},
                {"failhard": True},
            ]
        },
        "/etc/systemd/system/ttyd-registration.service": {
            "file.managed": [
                {"source": "salt://ttyd/templates/ttyd-instance.service.j2"},
                {"template": "jinja"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {
                    "context": {
                        "service": {
                            "user": "ttyd",
                            "group": "ttyd",
                            "uid": 984,
                            "gid": 978,
                            "shell": "/usr/sbin/nologin",
                            "home": "/var/lib/ttyd",
                            "system_user": True,
                            "create_home": False,
                            "unit_directory": "/etc/systemd/system",
                            "protect_clock": True,
                            "protect_kernel_logs": True,
                            "restrict_realtime": True,
                            "system_call_architectures": "native",
                        },
                        "instance_name": "registration",
                        "run_user": "ttyd",
                        "run_group": "ttyd",
                        "auth_header": "",
                        "private_tmp": True,
                        "protect_home": True,
                        "read_write_paths": ["/var/lib/ttyd"],
                        "index": "",
                        "client_options": [],
                        "server": {
                            "domain": "lf2607.kolamayermakers.org",
                            "host": "127.0.0.1",
                            "port": 7681,
                        },
                        "command": (
                            "/usr/bin/ssh -tt -o PreferredAuthentications=none "
                            "-o StrictHostKeyChecking=no "
                            "-o UserKnownHostsFile=/dev/null -o LogLevel=ERROR "
                            "new@localhost"
                        ),
                    }
                },
                {
                    "require": [
                        {"test": "ttyd::instances::required_pillar"},
                        {"test": "ttyd::instance::registration::required_pillar"},
                    ]
                },
            ]
        },
        "ttyd::instance::registration::systemd_daemon_reload": {
            "module.run": [
                {"service.systemctl_reload": []},
                {
                    "onchanges": [
                        {"file": "/etc/systemd/system/ttyd-registration.service"}
                    ]
                },
            ]
        },
        "ttyd::instance::registration::service": {
            "service.running": [
                {"name": "ttyd-registration"},
                {"enable": True},
                {
                    "require": [
                        {"packages": "ttyd"},
                        {"file": "ttyd::home"},
                        {"file": "/etc/systemd/system/ttyd-registration.service"},
                        {
                            "module": (
                                "ttyd::instance::registration::systemd_daemon_reload"
                            )
                        },
                        {"test": "ttyd::instances::required_pillar"},
                        {"test": "ttyd::instance::registration::required_pillar"},
                    ]
                },
                {
                    "watch": [
                        {"packages": "ttyd"},
                        {"file": "/etc/systemd/system/ttyd-registration.service"},
                    ]
                },
            ]
        },
        "ttyd::instance::ssh::required_pillar": {
            "test.check_pillar": [
                {
                    "string": [
                        "ttyd:instances:ssh:command",
                        "ttyd:instances:ssh:server:socket",
                        "ttyd:instances:ssh:server:socket_owner",
                        "ttyd:instances:ssh:server:domain",
                        "ttyd:instances:ssh:server:url",
                        "ttyd:instances:ssh:auth_header",
                        "ttyd:instances:ssh:index",
                        "ttyd:instances:ssh:run_user",
                        "ttyd:instances:ssh:run_group",
                    ]
                },
                {"boolean": ["ttyd:instances:ssh:private_tmp"]},
                {"boolean": ["ttyd:instances:ssh:protect_home"]},
                {"listing": ["ttyd:instances:ssh:client_options"]},
                {"failhard": True},
            ]
        },
        "/usr/local/sbin/ttyd-ssh-sso": {
            "file.managed": [
                {"source": "salt://roles/kam-classroom/templates/ttyd_ssh_sso.sh.j2"},
                {"template": "jinja"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {"context": {"web_ssh_url": "https://lf2607.kolamayermakers.org/ssh/"}},
                {"require": [{"test": "ttyd::instance::ssh::required_pillar"}]},
            ]
        },
        "/etc/systemd/system/ttyd-ssh.service": {
            "file.managed": [
                {"source": "salt://ttyd/templates/ttyd-instance.service.j2"},
                {"template": "jinja"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {
                    "context": {
                        "service": {
                            "user": "ttyd",
                            "group": "ttyd",
                            "uid": 984,
                            "gid": 978,
                            "shell": "/usr/sbin/nologin",
                            "home": "/var/lib/ttyd",
                            "system_user": True,
                            "create_home": False,
                            "unit_directory": "/etc/systemd/system",
                            "protect_clock": True,
                            "protect_kernel_logs": True,
                            "restrict_realtime": True,
                            "system_call_architectures": "native",
                        },
                        "instance_name": "ssh",
                        "server": {
                            "domain": "lf2607.kolamayermakers.org",
                            "url": "https://lf2607.kolamayermakers.org/ssh/",
                            "socket": "/run/ttyd-ssh/ssh.sock",
                            "socket_owner": "caddy:caddy",
                            "upstream": "unix//run/ttyd-ssh/ssh.sock",
                        },
                        "command": "/usr/local/sbin/ttyd-ssh-sso",
                        "run_user": "root",
                        "run_group": "root",
                        "auth_header": "X-WEBAUTH-USER",
                        "private_tmp": False,
                        "protect_home": False,
                        "read_write_paths": ["/var/lib/ttyd", "/home", "/tmp"],
                        "index": "/var/lib/ttyd/index.html",
                        "client_options": ["fontFamily=HackNerdFontMono,monospace"],
                    }
                },
                {
                    "require": [
                        {"test": "ttyd::instances::required_pillar"},
                        {"test": "ttyd::instance::ssh::required_pillar"},
                        {"file": "/usr/local/sbin/ttyd-ssh-sso"},
                    ]
                },
            ]
        },
        "ttyd::instance::ssh::systemd_daemon_reload": {
            "module.run": [
                {"service.systemctl_reload": []},
                {"onchanges": [{"file": "/etc/systemd/system/ttyd-ssh.service"}]},
            ]
        },
        "ttyd::instance::ssh::service": {
            "service.running": [
                {"name": "ttyd-ssh"},
                {"enable": True},
                {
                    "require": [
                        {"packages": "ttyd"},
                        {"file": "ttyd::home"},
                        {"file": "/etc/systemd/system/ttyd-ssh.service"},
                        {"module": "ttyd::instance::ssh::systemd_daemon_reload"},
                        {"test": "ttyd::instances::required_pillar"},
                        {"test": "ttyd::instance::ssh::required_pillar"},
                        {"cmd": "ttyd::web::custom_index::initial"},
                        {"cmd": "ttyd::web::custom_index::updated"},
                        {"file": "ttyd::web::custom_index::file"},
                    ]
                },
                {
                    "watch": [
                        {"packages": "ttyd"},
                        {"file": "/etc/systemd/system/ttyd-ssh.service"},
                        {"file": "/usr/local/sbin/ttyd-ssh-sso"},
                        {"cmd": "ttyd::web::custom_index::initial"},
                        {"cmd": "ttyd::web::custom_index::updated"},
                    ]
                },
            ]
        },
    }
