"""Tests for Kolam Ayer Makers classroom role."""

from __future__ import annotations

import importlib
import json
import os
import shlex
import subprocess
import tomllib
from collections.abc import MutableMapping
from pathlib import Path
from typing import Protocol, TypeGuard, cast

import pytest
from salt.utils.requisite import DependencyGraph, RequisiteType  # pyright: ignore[reportMissingTypeStubs]

from tests.support.paths import SALTSTACK_DIRECTORY


class _Template(Protocol):
    def render(self, **context: object) -> str:
        """Render the template with test context."""
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
    def __init__(self, pillar: dict[str, object]) -> None:
        self._pillar: dict[str, object] = pillar

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


def _environment() -> _Environment:
    jinja2 = importlib.import_module("jinja2")
    environment_factory = cast(_EnvironmentFactory, getattr(jinja2, "Environment"))
    loader_factory = cast(_LoaderFactory, getattr(jinja2, "FileSystemLoader"))
    environment = environment_factory(
        loader=loader_factory(str(SALTSTACK_DIRECTORY / "states")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["yaml"] = _yaml_filter
    return environment


def _yaml_filter(value: object) -> str:
    yaml_module = cast(_YamlModule, cast(object, importlib.import_module("yaml")))
    return (
        yaml_module.safe_dump(value, default_flow_style=True)
        .strip()
        .removesuffix("\n...")
    )


def _load_state(template: str, pillar: dict[str, object]) -> dict[str, object]:
    yaml_module = cast(_YamlModule, cast(object, importlib.import_module("yaml")))
    return cast(
        dict[str, object],
        yaml_module.safe_load(
            _environment().get_template(template).render(salt=_SaltNamespace(pillar))
        ),
    )


def _load_pillar_file(
    relative_path: str,
    *,
    grains_id: str = "production-host",
    deployment_environment: str = "production",
) -> object:
    jinja2 = importlib.import_module("jinja2")
    environment_factory = cast(_EnvironmentFactory, getattr(jinja2, "Environment"))
    loader_factory = cast(_LoaderFactory, getattr(jinja2, "FileSystemLoader"))
    environment = environment_factory(
        loader=loader_factory(str(SALTSTACK_DIRECTORY / "pillar")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    yaml_module = cast(_YamlModule, cast(object, importlib.import_module("yaml")))
    return yaml_module.safe_load(
        environment.get_template(relative_path.removeprefix("pillar/")).render(
            grains={
                "id": grains_id,
                "deployment_environment": deployment_environment,
            }
        )
    )


def _state_arguments(state: object, function: str) -> dict[str, object]:
    return {
        key: value
        for argument in cast(dict[str, list[dict[str, object]]], state)[function]
        for key, value in argument.items()
    }


def _role_pillar(
    relative_path: str,
    pillar_key: str,
    grains_id: str,
    deployment_environment: str = "production",
) -> dict[str, object]:
    return cast(
        dict[str, object],
        cast(
            dict[str, object],
            _load_pillar_file(
                relative_path,
                grains_id=grains_id,
                deployment_environment=deployment_environment,
            ),
        )[pillar_key],
    )


def _forgejo_authelia_require(
    grains_id: str, deployment_environment: str = "production"
) -> list[dict[str, str]]:
    forgejo = _role_pillar(
        "pillar/roles/kam-classroom/forgejo.sls",
        "forgejo",
        grains_id,
        deployment_environment,
    )
    oauth_sources = cast(dict[str, object], forgejo["oauth_sources"])
    authelia = cast(dict[str, object], oauth_sources["authelia"])
    return cast(list[dict[str, str]], authelia["require"])


def _forgejo_server() -> dict[str, object]:
    return {
        "domain": "lf2607.kolamayermakers.org",
        "http_address": "127.0.0.1",
        "http_port": 3000,
        "logout_redirect": "/git/.kam-classroom/logout",
    }


def _lldap_http() -> dict[str, object]:
    return {
        "domain": "lf2607.kolamayermakers.org",
        "host": "127.0.0.1",
        "port": 17170,
        "url": "https://lf2607.kolamayermakers.org/lldap/",
    }


def _authelia_server() -> dict[str, object]:
    return {
        "domain": "lf2607.kolamayermakers.org",
        "host": "127.0.0.1",
        "port": 9091,
        "path": "/auth",
        "url": "https://lf2607.kolamayermakers.org/auth/",
    }


def _gamja_paths() -> dict[str, object]:
    return {
        "web_root": "/var/www/gamja",
    }


def _ergo_server() -> dict[str, object]:
    return {
        "name": "lf2607.kolamayermakers.org",
    }


def _ergo_listeners() -> dict[str, object]:
    return {
        "websocket": {
            "address": "127.0.0.1:8097",
        }
    }


def _ttyd_server() -> dict[str, object]:
    return {
        "domain": "lf2607.kolamayermakers.org",
        "host": "127.0.0.1",
        "port": 7681,
    }


def _ssh_ttyd_server() -> dict[str, object]:
    return {
        "domain": "lf2607.kolamayermakers.org",
        "url": "https://lf2607.kolamayermakers.org/ssh/",
        "upstream": "unix//run/ttyd-ssh/ssh.sock",
    }


def _ttyd_web_assets() -> dict[str, object]:
    return {
        "route": "/ssh/ttyd-assets",
        "directory": "/var/lib/ttyd/assets",
    }


def _irc_pillar() -> dict[str, object]:
    return {
        "ergo": {
            "service": {
                "user": "ergo",
                "group": "ergo",
            },
            "paths": {
                "cert_sync_script": "/usr/local/sbin/ergo-sync-caddy-cert",
                "cert_sync_service": "/etc/systemd/system/ergo-sync-caddy-cert.service",
                "cert_sync_timer": "/etc/systemd/system/ergo-sync-caddy-cert.timer",
                "tls_directory": "/etc/ergo/tls",
                "certificate_file": "/etc/ergo/tls/fullchain.pem",
                "certificate_key_file": "/etc/ergo/tls/privkey.pem",
            },
            "server": {
                "name": "irc.kolamayermakers.org",
            },
            "listeners": {
                "irc": {
                    "address": ":6697",
                }
            },
        }
    }


def _kam_classroom_pillar() -> dict[str, object]:
    return {
        "kam_classroom": {
            "backup": {
                "root": "/var/backups/kam-classroom",
                "retention_days": 14,
                "maker_guide_database": "/var/lib/maker-guide/state.db",
                "maker_guide_config": "/etc/maker-guide/config.toml",
                "ergo_data": "/data/ergo",
                "lldap_data": "/data/lldap",
                "authelia_data": "/data/authelia",
                "forgejo_data": "/data/forgejo",
                "homes_data": "/home",
            },
            "bot": {
                "irc_account": "guide",
                "irc_channels": ["#lf2607"],
                "openrouter_api_key": "sk-or-test",
                "docs_site": {
                    "directory": "/var/www/maker-guide-docs",
                    "output": "/var/www/maker-guide-docs/current",
                },
                "sync_derived_data": {
                    "makers_root": "/makers",
                    "documents_root": "/docs",
                    "service_file": (
                        "/etc/systemd/system/maker-guide-sync-derived-data.service"
                    ),
                    "timer_file": (
                        "/etc/systemd/system/maker-guide-sync-derived-data.timer"
                    ),
                    "on_boot": "1m",
                    "on_unit_active": "1m",
                    "accuracy": "30s",
                },
                "openrouter_egress": {
                    "nftables_file": (
                        "/etc/nftables.d/47-maker-guide-openrouter-egress.nft"
                    ),
                    "header": "# Maker Guide OpenRouter egress policy",
                    "destination": "maker-guide-openrouter",
                    "set_v4": "maker_guide_openrouter_v4",
                    "set_v6": "maker_guide_openrouter_v6",
                    "destination_position": "27",
                    "domain_position": "67",
                    "tcp_port": 443,
                    "domains": ["openrouter.ai"],
                },
            },
            "domain": {"public_domain": "kolamayermakers.org"},
            "npm_egress": {
                "nftables_file": "/etc/nftables.d/48-classroom-npm-egress.nft",
                "header": "# Classroom npm registry egress policy",
                "destination": "classroom-npm",
                "set_v4": "classroom_npm_v4",
                "set_v6": "classroom_npm_v6",
                "destination_position": "28",
                "domain_position": "68",
                "gid": 1001,
                "user": "maker-guide",
                "tcp_port": 443,
                "domains": ["registry.npmjs.org"],
            },
            "identity": {
                "registration_user": {
                    "user": "new",
                    "group": "new",
                    "uid": 986,
                    "gid": 980,
                },
                "registration_administrator": "pmuller",
                "default_group": "humans",
                "lingering": {
                    "group": "linux-foundations",
                    "uid_minimum": 10000,
                    "uid_maximum": 20999,
                    "packages": ["libpam-systemd", "dbus-user-session"],
                },
                "groups": {
                    "humans": {
                        "gid_number": 1001,
                    },
                    "makers": {
                        "gid_number": 1002,
                    },
                    "architects": {
                        "gid_number": 1003,
                    },
                    "speakers": {
                        "gid_number": 1004,
                    },
                    "lf2607": {
                        "gid_number": 1007,
                    },
                    "admins": {
                        "gid_number": 1008,
                    },
                    "mentors": {
                        "gid_number": 1009,
                    },
                    "pa": {
                        "gid_number": 1010,
                    },
                    "volunteers": {
                        "gid_number": 1011,
                    },
                    "linux-foundations": {
                        "gid_number": 1012,
                    },
                    "students": {
                        "gid_number": 1013,
                    },
                    "guide": {
                        "gid_number": 9000,
                    },
                    "irc-bots": {
                        "gid_number": 9001,
                    },
                },
                "managed_users": {
                    "pmuller": {
                        "uid_number": 10009,
                        "display_name": "Philippe Muller",
                        "email": "philippe.muller@kam-classroom-dev",
                        "home_directory": "/home/pmuller",
                        "shell": "/bin/bash",
                        "primary_group": "humans",
                        "secondary_groups": ["mentors", "admins", "linux-foundations"],
                        "ssh_public_keys": ["ssh-rsa AAAATEST cardno:25_939_134"],
                    },
                    "wanlong": {
                        "uid_number": 10010,
                        "display_name": "Wanlong",
                        "email": "liwanlong@protonmail.com",
                        "home_directory": "/home/wanlong",
                        "shell": "/bin/bash",
                        "primary_group": "humans",
                        "secondary_groups": ["mentors", "linux-foundations"],
                        "ssh_public_keys": ["ssh-rsa AAAATEST wanlong"],
                    },
                    "guide": {
                        "uid_number": 9000,
                        "display_name": "TheGuide",
                        "email": "guide@kam-classroom-dev",
                        "home_directory": "/var/lib/guide",
                        "shell": "/usr/sbin/nologin",
                        "primary_group": "guide",
                        "secondary_groups": ["irc-bots"],
                    },
                },
            },
        },
        "dns-nftsets": {
            "configuration": {
                "path": "/etc/dns-nftsets/configuration.jsonl",
                "set_timeout": "24h",
            }
        },
    }


def _caddy_pillar() -> dict[str, object]:
    return {
        "caddy": _role_pillar("pillar/caddy.sls", "caddy", "production-host")
        | _role_pillar(
            "pillar/roles/kam-classroom/caddy.sls", "caddy", "production-host"
        ),
        "forgejo": {"server": _forgejo_server()},
        "lldap": {"http": _lldap_http()},
        "authelia": {"server": _authelia_server()},
        "gamja": {"paths": _gamja_paths()},
        "ergo": {"server": _ergo_server(), "listeners": _ergo_listeners()},
        "ttyd": {
            "instances": {
                "registration": {"server": _ttyd_server()},
                "ssh": {"server": _ssh_ttyd_server()},
            },
            "web": {"assets": _ttyd_web_assets()},
        },
    }


def test_role_composes_debian_base_and_classroom_services() -> None:
    """Test that role deploys the base system and classroom services."""
    assert _load_state("roles/kam-classroom/init.sls", {}) == {
        "include": [
            "apt",
            "apt.firewall",
            "bootstrap.packages",
            "presets.base",
            "unbound",
            "dns-nftsets",
            "systemd-timesyncd",
            "openssh-server",
            "pam-pwquality",
            "roles.kam-classroom.packages",
            "roles.kam-classroom.git",
            "roles.kam-classroom.tldr",
            "roles.kam-classroom.data",
            "roles.kam-classroom.backup",
            "systemd.drop_ins",
            "quotas",
            "rsyslog.cleanup",
            "roles.kam-classroom.kolam-makers-logo",
            "roles.kam-classroom.hosts",
            "forgejo",
            "roles.kam-classroom.identity",
            "authelia",
            "gamja",
            "roles.kam-classroom.caddy",
            "ergo",
            "roles.kam-classroom.irc",
            "roles.kam-classroom.npm",
            "roles.kam-classroom.network-diagnostics",
            "nftables",
            "root",
            "htop",
            "terminfo",
            "uv",
            "roles.kam-classroom.bot",
        ]
    }


def test_network_diagnostics_uses_pillar_packages_and_identity_group() -> None:
    """Diagnostic tools join bootstrap; UDP access follows identity, not a fixed GID."""
    packages = ["test-curl", "test-traceroute"]
    state = _load_state(
        "roles/kam-classroom/network-diagnostics.sls",
        {
            "kam_classroom": {
                "identity": {"groups": {"humans": {"gid_number": 2042}}},
                "network_diagnostics": {
                    "packages": packages,
                    "traceroute": {
                        "firewall_file": "/etc/nftables.d/50-test-traceroute.nft",
                        "udp_port_range": "33434-33534",
                    },
                },
            }
        },
    )
    for package in packages:
        arguments = cast(
            dict[str, list[dict[str, object]]],
            state[f"kam-classroom::network-diagnostics::{package}"],
        )["pkg.installed"]
        assert {"name": package} in arguments
        assert {
            "require": [
                {"module": "apt::refresh"},
                {"test": "bootstrap::package_sources_ready"},
                {"test": "kam-classroom::network-diagnostics::required-pillar"},
            ]
        } in arguments
        assert {"require_in": [{"test": "bootstrap::apt_packages_ready"}]} in arguments

    firewall = cast(
        dict[str, list[dict[str, object]]],
        state["kam-classroom::network-diagnostics::traceroute-firewall"],
    )["nftables_file.managed"]
    assert {"name": "/etc/nftables.d/50-test-traceroute.nft"} in firewall
    assert {
        "rules": [
            {
                "chain": "output",
                "position": "10",
                "rule": (
                    "meta skgid 2042 udp dport 33434-33534 "
                    'counter name "output_kam_classroom_traceroute" accept '
                    'comment "classroom users traceroute udp"'
                ),
            }
        ]
    } in firewall


def test_firewall_validation_gates_startup_and_reload() -> None:
    """Rules validate after packages are ready and before startup or reload."""
    state = cast(
        dict[str, dict[str, list[dict[str, object]]]],
        _load_state("nftables/service.sls", {}),
    )
    assert {"require": [{"test": "bootstrap::apt_packages_ready"}]} in state[
        "nftables::validate"
    ]["cmd.run"]
    assert state["nftables::validate_startup"]["cmd.run"] == [
        {"name": "nft -c -f /etc/nftables.conf"},
        {"unless": "systemctl is-active --quiet nftables"},
        {"require": [{"cmd": "nftables::validate"}]},
    ]
    assert {
        "require": [
            {"pkg": "nftables"},
            {"file": "/etc/nftables.conf"},
            {"test": "bootstrap::apt_packages_ready"},
            {"cmd": "nftables::validate_startup"},
        ]
    } in state["nftables::service"]["service.running"]
    assert {"require": [{"service": "nftables::service"}]} in state["nftables::reload"][
        "cmd.run"
    ]
    assert {"onchanges": [{"cmd": "nftables::validate"}]} in state["nftables::reload"][
        "cmd.run"
    ]


@pytest.mark.parametrize("fragment_type", ["file", "nftables_file"])
def test_firewall_fragment_requisites_resolve_by_name(fragment_type: str) -> None:
    """Salt resolves symbolic fragment IDs, including with zero custom states."""
    validation: dict[str, object] = {
        "state": "cmd",
        "fun": "run",
        "__id__": "nftables::validate",
    }
    for argument in cast(
        dict[str, list[dict[str, object]]],
        _load_state("nftables/service.sls", {})["nftables::validate"],
    )["cmd.run"]:
        validation.update(argument)
    graph = DependencyGraph()
    graph.add_chunk(validation, allow_aggregate=False)
    for index, (state_type, name) in enumerate(
        [
            ("test", "bootstrap::apt_packages_ready"),
            ("file", "/etc/nftables.conf"),
            ("file", "/etc/nftables.d/99-default-input-log.nft"),
            (fragment_type, "/etc/nftables.d/50-test.nft"),
        ]
    ):
        graph.add_chunk(
            {
                "state": state_type,
                "fun": "nop",
                "__id__": f"test::fragment::{index}",
                "name": name,
            },
            allow_aggregate=False,
        )
    assert graph.add_requisites(validation, []) is None
    assert {
        dependency["name"]
        for requisite_type, dependency in graph.get_dependencies(validation)
        if requisite_type == RequisiteType.ONCHANGES
    } == {
        "/etc/nftables.conf",
        "/etc/nftables.d/99-default-input-log.nft",
        "/etc/nftables.d/50-test.nft",
    }


def test_role_configures_git_default_branch() -> None:
    """Classroom Git initializes new repositories on the course branch."""
    pillar = cast(
        dict[str, object],
        _load_pillar_file("pillar/roles/kam-classroom/git.sls"),
    )
    state = _load_state("roles/kam-classroom/git.sls", pillar)

    assert state == {
        "roles::kam_classroom::git::required_pillar": {
            "test.check_pillar": [
                {"string": ["kam_classroom:git:default_branch"]},
                {"failhard": True},
            ]
        },
        "roles::kam_classroom::git::default_branch": {
            "cmd.run": [
                {"name": "/usr/bin/git config --system init.defaultBranch main"},
                {
                    "unless": (
                        '/usr/bin/test "$(/usr/bin/git config --system --get '
                        'init.defaultBranch)" = main'
                    )
                },
                {"require": [{"test": "roles::kam_classroom::git::required_pillar"}]},
            ]
        },
    }


def test_role_bot_installs_maker_guide_artifact() -> None:
    """Test that maker-guide is installed, configured, and run as a service."""
    pillar = _kam_classroom_pillar()
    pillar["ergo"] = {
        "server": {"name": "irc.kolamayermakers.org"},
        "channels": {"managed": ["#kolamayermakers", "#lf2607"]},
    }
    state = _load_state("roles/kam-classroom/bot.sls", pillar)

    assert state["include"] == [
        "roles.kam-classroom.identity",
        "roles.kam-classroom.caddy.service",
        "dns-nftsets.configuration",
        "dns-nftsets.service",
        "nftables",
    ]
    assert state["roles::kam_classroom::bot::required_pillar"] == {
        "test.check_pillar": [
            {
                "string": [
                    "dns-nftsets:configuration:path",
                    "dns-nftsets:configuration:set_timeout",
                    "ergo:server:name",
                    "kam_classroom:bot:irc_account",
                    "kam_classroom:bot:openrouter_api_key",
                    "kam_classroom:bot:openrouter_egress:nftables_file",
                    "kam_classroom:bot:openrouter_egress:header",
                    "kam_classroom:bot:openrouter_egress:destination",
                    "kam_classroom:bot:openrouter_egress:set_v4",
                    "kam_classroom:bot:openrouter_egress:set_v6",
                    "kam_classroom:bot:openrouter_egress:destination_position",
                    "kam_classroom:bot:openrouter_egress:domain_position",
                    "kam_classroom:bot:docs_site:directory",
                    "kam_classroom:bot:docs_site:output",
                    "kam_classroom:bot:sync_derived_data:makers_root",
                    "kam_classroom:bot:sync_derived_data:documents_root",
                    "kam_classroom:bot:sync_derived_data:service_file",
                    "kam_classroom:bot:sync_derived_data:timer_file",
                    "kam_classroom:bot:sync_derived_data:on_boot",
                    "kam_classroom:bot:sync_derived_data:on_unit_active",
                    "kam_classroom:bot:sync_derived_data:accuracy",
                ]
            },
            {"integer": ["kam_classroom:bot:openrouter_egress:tcp_port"]},
            {
                "listing": [
                    "kam_classroom:bot:irc_channels",
                    "kam_classroom:bot:openrouter_egress:domains",
                ]
            },
            {"failhard": True},
        ]
    }
    assert state["roles::kam_classroom::bot::group"] == {
        "group.present": [{"name": "maker-guide"}, {"system": True}]
    }
    assert state["roles::kam_classroom::bot::user"] == {
        "user.present": [
            {"name": "maker-guide"},
            {"gid": "maker-guide"},
            {"home": "/var/lib/maker-guide"},
            {"shell": "/usr/sbin/nologin"},
            {"createhome": False},
            {"system": True},
            {"require": [{"group": "roles::kam_classroom::bot::group"}]},
        ]
    }
    assert state["roles::kam_classroom::bot::openrouter_dns_nftsets"] == {
        "dns_nftsets.fragment": [
            {"target": "/etc/dns-nftsets/configuration.jsonl"},
            {"destination_position": 27},
            {"domain_position": 67},
            {
                "destinations": {
                    "maker-guide-openrouter": {
                        "family": "inet",
                        "table": "filter",
                        "set_v4": "maker_guide_openrouter_v4",
                        "set_v6": "maker_guide_openrouter_v6",
                    }
                }
            },
            {
                "domains": [
                    {
                        "exact": "openrouter.ai",
                        "destination": "maker-guide-openrouter",
                    }
                ]
            },
            {"require_in": [{"concat": "dns-nftsets::configuration_file"}]},
            {"require": [{"test": "roles::kam_classroom::bot::required_pillar"}]},
        ]
    }
    assert state["roles::kam_classroom::bot::openrouter_egress"] == {
        "nftables_file.managed": [
            {"name": "/etc/nftables.d/47-maker-guide-openrouter-egress.nft"},
            {"header": "# Maker Guide OpenRouter egress policy"},
            {"counters": ["output_maker_guide_openrouter"]},
            {
                "sets": [
                    {
                        "name": "maker_guide_openrouter_v4",
                        "type": "ipv4_addr",
                        "flags": ["timeout"],
                        "timeout": "24h",
                        "position": "25",
                    },
                    {
                        "name": "maker_guide_openrouter_v6",
                        "type": "ipv6_addr",
                        "flags": ["timeout"],
                        "timeout": "24h",
                        "position": "25",
                    },
                ]
            },
            {"chains": [{"name": "output", "position": "60"}]},
            {
                "rules": [
                    {
                        "chain": "output",
                        "position": "10",
                        "rule": (
                            "meta skuid maker-guide ip daddr "
                            "@maker_guide_openrouter_v4 tcp dport 443 counter "
                            'name "output_maker_guide_openrouter" accept '
                            'comment "maker-guide openrouter"'
                        ),
                    },
                    {
                        "chain": "output",
                        "position": "11",
                        "rule": (
                            "meta skuid maker-guide ip6 daddr "
                            "@maker_guide_openrouter_v6 tcp dport 443 counter "
                            'name "output_maker_guide_openrouter" accept '
                            'comment "maker-guide openrouter"'
                        ),
                    },
                ]
            },
            {"user": "root"},
            {"group": "root"},
            {"mode": "0644"},
            {
                "require": [
                    {"file": "/etc/nftables.d"},
                    {"test": "roles::kam_classroom::bot::required_pillar"},
                    {"user": "roles::kam_classroom::bot::user"},
                ]
            },
            {"require_in": [{"cmd": "dns-nftsets::service"}]},
            {"onchanges_in": [{"cmd": "nftables::reload"}]},
            {"watch_in": [{"cmd": "nftables::validate"}]},
        ]
    }
    assert state["roles::kam_classroom::bot::executable_directory"] == {
        "file.directory": [
            {"name": "/usr/local/lib/maker-guide"},
            {"user": "root"},
            {"group": "root"},
            {"mode": "0755"},
            {"makedirs": True},
        ]
    }
    assert state["roles::kam_classroom::bot::release_directory"] == {
        "file.directory": [
            {"name": "/usr/local/lib/maker-guide/releases"},
            {"user": "root"},
            {"group": "root"},
            {"mode": "0755"},
            {"makedirs": True},
            {"require": [{"file": "roles::kam_classroom::bot::executable_directory"}]},
        ]
    }
    assert state["roles::kam_classroom::bot::incoming_release"] == {
        "file.recurse": [
            {"name": "/usr/local/lib/maker-guide/incoming"},
            {"source": "salt://roles/kam-classroom/files/maker-guide"},
            {"clean": True},
            {"user": "root"},
            {"group": "root"},
            {"file_mode": "0644"},
            {"dir_mode": "0755"},
            {
                "require": [
                    {"file": "roles::kam_classroom::bot::executable_directory"},
                    {"test": "roles::kam_classroom::bot::required_pillar"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::stage_release"] == {
        "cmd.run": [
            {
                "name": (
                    "/usr/local/sbin/maker-guide-release "
                    "/usr/local/lib/maker-guide/incoming "
                    "/usr/local/lib/maker-guide/releases stage"
                )
            },
            {
                "unless": (
                    "/usr/local/sbin/maker-guide-release "
                    "/usr/local/lib/maker-guide/incoming "
                    "/usr/local/lib/maker-guide/releases staged"
                )
            },
            {
                "require": [
                    {"file": "roles::kam_classroom::bot::incoming_release"},
                    {"file": "roles::kam_classroom::bot::release_directory"},
                    {"file": "/usr/local/sbin/maker-guide-release"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::stop_for_release"] == {
        "cmd.run": [
            {
                "name": (
                    "/usr/local/sbin/maker-guide-release "
                    "/usr/local/lib/maker-guide/incoming "
                    '/usr/local/lib/maker-guide/releases stop "new"'
                )
            },
            {
                "unless": (
                    "/usr/local/sbin/maker-guide-release "
                    "/usr/local/lib/maker-guide/incoming "
                    "/usr/local/lib/maker-guide/releases active"
                )
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::stage_release"},
                    {"user": "roles::kam_classroom::registration_user"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::publish_release"] == {
        "cmd.run": [
            {
                "name": (
                    "/usr/local/sbin/maker-guide-release "
                    "/usr/local/lib/maker-guide/incoming "
                    "/usr/local/lib/maker-guide/releases activate"
                )
            },
            {
                "unless": (
                    "/usr/local/sbin/maker-guide-release "
                    "/usr/local/lib/maker-guide/incoming "
                    "/usr/local/lib/maker-guide/releases active"
                )
            },
            {"require": [{"cmd": "roles::kam_classroom::bot::stop_for_release"}]},
        ]
    }
    assert state["roles::kam_classroom::bot::release_pending"] == {
        "cmd.run": [
            {"name": "/usr/bin/true"},
            {
                "onlyif": (
                    "/usr/local/sbin/maker-guide-release "
                    "/usr/local/lib/maker-guide/incoming "
                    "/usr/local/lib/maker-guide/releases pending"
                )
            },
            {"require": [{"cmd": "roles::kam_classroom::bot::publish_release"}]},
        ]
    }
    assert state["/var/www/maker-guide-docs"] == {
        "file.directory": [
            {"user": "maker-guide"},
            {"group": "humans"},
            {"mode": "0755"},
            {"makedirs": True},
            {
                "require": [
                    {"user": "roles::kam_classroom::bot::user"},
                    {"service": "sssd::service"},
                ]
            },
        ]
    }
    assert state["/var/www/maker-guide-docs/current"] == {
        "file.directory": [
            {"user": "maker-guide"},
            {"group": "humans"},
            {"mode": "0755"},
            {"makedirs": True},
            {"require": [{"file": "/var/www/maker-guide-docs"}]},
        ]
    }
    for command in (
        "maker-guide-bot",
        "maker-guide-bash-hook",
        "maker-guide-build-docs",
        "maker-guide-build-personal-website",
        "maker-guide-calendar",
        "maker-guide-create-learner",
        "maker-guide-db",
        "maker-guide-export-audit",
        "maker-guide-help",
        "maker-guide-initialize-learner",
        "maker-guide-grant-group",
        "maker-guide-prune-llm-audit",
        "maker-guide-prune-observations",
        "maker-guide-ops",
        "maker-guide-progress",
        "maker-guide-register",
        "maker-guide-registration",
        "maker-guide-revoke-group",
        "maker-guide-sync-derived-data",
        "maker-guide-sync-groups",
    ):
        symlink = _state_arguments(state[f"/usr/local/bin/{command}"], "file.symlink")
        assert symlink["target"] == f"/usr/local/lib/maker-guide/current/bin/{command}"
        assert symlink["force"] is True
        assert {"cmd": "roles::kam_classroom::bot::publish_release"} in cast(
            list[dict[str, str]], symlink["require"]
        )
        if command == "maker-guide-create-learner":
            assert {"cmd": "roles::kam_classroom::identity::lingering"} in cast(
                list[dict[str, str]], symlink["require"]
            )
    config_state = cast(dict[str, object], state["/etc/maker-guide/config.toml"])
    assert config_state["file.managed"] == [
        {"source": "salt://roles/kam-classroom/templates/maker-guide-config.toml.j2"},
        {"template": "jinja"},
        {"user": "root"},
        {"group": "maker-guide"},
        {"mode": "0644"},
        {
            "context": {
                "socket_path": "/run/maker-guide/preexec.sock",
                "runtime_group": "humans",
                "database_path": "/var/lib/maker-guide/state.db",
                "irc_server": "irc.kolamayermakers.org",
                "irc_channels": ["#lf2607"],
                "irc_password_file": "/etc/maker-guide/secrets/irc-password",
                "irc_account": "guide",
                "llm_tutor_enabled": True,
            }
        },
        {
            "require": [
                {"file": "roles::kam_classroom::bot::configuration_directory"},
                {"file": "roles::kam_classroom::bot::data_directory"},
                {"file": "/etc/maker-guide/secrets/irc-password"},
                {"file": "/etc/maker-guide/secrets/openrouter-api-key"},
            ]
        },
    ]
    assert state["/etc/maker-guide/secrets/openrouter-api-key"] == {
        "file.managed": [
            {"user": "root"},
            {"group": "maker-guide"},
            {"mode": "0640"},
            {"contents": "sk-or-test\n"},
            {"require": [{"file": "roles::kam_classroom::bot::secrets_directory"}]},
        ]
    }
    assert state["roles::kam_classroom::bot::irc_password_generated"] == {
        "cmd.run": [
            {
                "name": (
                    "/usr/bin/python3 <<'PYTHON'\n"
                    "from pathlib import Path\n"
                    "import secrets\n\n"
                    'Path("/etc/maker-guide/secrets/irc-password").write_text(\n'
                    '    secrets.token_urlsafe(48) + "\\n",\n'
                    '    encoding="utf-8",\n'
                    ")\n"
                    "PYTHON\n"
                )
            },
            {"unless": "test -s /etc/maker-guide/secrets/irc-password"},
            {"require": [{"file": "roles::kam_classroom::bot::secrets_directory"}]},
        ]
    }
    assert state["/etc/maker-guide/secrets/irc-password"] == {
        "file.managed": [
            {"user": "root"},
            {"group": "maker-guide"},
            {"mode": "0640"},
            {"replace": False},
            {"require": [{"cmd": "roles::kam_classroom::bot::irc_password_generated"}]},
        ]
    }
    assert state["roles::kam_classroom::bot::guide_password"] == {
        "cmd.run": [
            {
                "name": (
                    "/usr/local/sbin/lldap-set-password guide --password-stdin < "
                    "/etc/maker-guide/secrets/irc-password"
                )
            },
            {
                "unless": (
                    "/usr/local/sbin/lldap-set-password guide --password-stdin "
                    "--check < /etc/maker-guide/secrets/irc-password"
                )
            },
            {
                "require": [
                    {"file": "/usr/local/sbin/lldap-set-password"},
                    {"file": "/etc/maker-guide/secrets/irc-password"},
                    {"cmd": "roles::kam_classroom::lldap_user::guide"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::data_directory"] == {
        "file.directory": [
            {"name": "/var/lib/maker-guide"},
            {"user": "maker-guide"},
            {"group": "mentors"},
            {"mode": "0750"},
            {"makedirs": True},
            {
                "require": [
                    {"cmd": "roles::kam_classroom::lldap_group::mentors"},
                    {"user": "roles::kam_classroom::bot::user"},
                    {"service": "sssd::service"},
                ]
            },
        ]
    }
    assert state["/var/lib/maker-guide/state.db"] == {
        "file.managed": [
            {"user": "maker-guide"},
            {"group": "mentors"},
            {"mode": "0640"},
            {"replace": False},
            {
                "require": [
                    {"cmd": "roles::kam_classroom::lldap_group::mentors"},
                    {"file": "roles::kam_classroom::bot::data_directory"},
                ]
            },
        ]
    }
    assert state["/makers"] == {
        "file.directory": [
            {"user": "maker-guide"},
            {"group": "humans"},
            {"mode": "0755"},
            {"makedirs": True},
            {
                "require": [
                    {"user": "roles::kam_classroom::bot::user"},
                    {"service": "sssd::service"},
                ]
            },
        ]
    }
    assert state["/docs"] == {
        "file.directory": [
            {"user": "maker-guide"},
            {"group": "humans"},
            {"mode": "0755"},
            {"makedirs": True},
            {
                "require": [
                    {"user": "roles::kam_classroom::bot::user"},
                    {"service": "sssd::service"},
                ]
            },
        ]
    }
    assert state["/etc/profile.d/maker-guide-bash-hook.sh"] == {
        "file.managed": [
            {"user": "root"},
            {"group": "root"},
            {"mode": "0644"},
            {
                "contents": (
                    'case "$-" in\n'
                    "  *i*) ;;\n"
                    "  *) return 0 ;;\n"
                    "esac\n\n"
                    'if [ -z "${BASH_VERSION:-}" ]; then\n'
                    "  return 0\n"
                    "fi\n\n"
                    "__maker_guide_hook_enabled=0\n"
                    "for __maker_guide_group in $(id -nG 2>/dev/null); do\n"
                    '  case "$__maker_guide_group" in\n'
                    "    linux-foundations)\n"
                    "      __maker_guide_hook_enabled=1\n"
                    "      break\n"
                    "      ;;\n"
                    "  esac\n"
                    "done\n\n"
                    'if [ "$__maker_guide_hook_enabled" = 1 ] && command -v maker-guide-bash-hook >/dev/null 2>&1; then\n'
                    '  eval "$(maker-guide-bash-hook init bash 2>/dev/null)" || true\n'
                    "fi\n\n"
                    'if [ "$__maker_guide_hook_enabled" = 1 ] && command -v maker-guide-build-personal-website >/dev/null 2>&1; then\n'
                    "  alias build-website='maker-guide-build-personal-website'\n"
                    "fi\n\n"
                    "unset __maker_guide_group __maker_guide_hook_enabled\n"
                )
            },
            {
                "require": [
                    {"file": "/usr/local/bin/maker-guide-bash-hook"},
                    {"file": "/usr/local/bin/maker-guide-build-personal-website"},
                    {"file": "/usr/local/bin/guide"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::database_migrate"] == {
        "cmd.run": [
            {
                "name": (
                    "/usr/local/bin/maker-guide-db --config "
                    "/etc/maker-guide/config.toml upgrade head"
                )
            },
            {"runas": "maker-guide"},
            {
                "unless": (
                    "/usr/local/bin/maker-guide-db --config "
                    "/etc/maker-guide/config.toml current --check-heads"
                )
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::publish_release"},
                    {"file": "/usr/local/bin/maker-guide-db"},
                    {"file": "/etc/maker-guide/config.toml"},
                    {"file": "/var/lib/maker-guide/state.db"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::initialize_participant::pmuller"] == {
        "cmd.run": [
            {
                "name": (
                    '/usr/local/bin/maker-guide-initialize-learner "pmuller" --uid 10009 '
                    '--enroll --not-rank-eligible --config "/etc/maker-guide/config.toml"'
                )
            },
            {"runas": "maker-guide"},
            {
                "unless": (
                    "/usr/bin/python3 -c 'import sqlite3,sys;sys.exit(sqlite3.connect("
                    'sys.argv[1]).execute( "select 1 from learners where handle = ?",'
                    '(sys.argv[2],)).fetchone() is None)\' "/var/lib/maker-guide/state.db" '
                    '"pmuller"'
                )
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::database_migrate"},
                    {"cmd": "roles::kam_classroom::lldap_user::pmuller"},
                    {"file": "/usr/local/bin/maker-guide-initialize-learner"},
                    {"file": "/etc/maker-guide/config.toml"},
                    {"file": "/var/lib/maker-guide/state.db"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::initialize_participant::wanlong"] == {
        "cmd.run": [
            {
                "name": (
                    '/usr/local/bin/maker-guide-initialize-learner "wanlong" --uid 10010 '
                    '--enroll --not-rank-eligible --config "/etc/maker-guide/config.toml"'
                )
            },
            {"runas": "maker-guide"},
            {
                "unless": (
                    "/usr/bin/python3 -c 'import sqlite3,sys;sys.exit(sqlite3.connect("
                    'sys.argv[1]).execute( "select 1 from learners where handle = ?",'
                    '(sys.argv[2],)).fetchone() is None)\' "/var/lib/maker-guide/state.db" '
                    '"wanlong"'
                )
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::database_migrate"},
                    {"cmd": "roles::kam_classroom::lldap_user::wanlong"},
                    {"file": "/usr/local/bin/maker-guide-initialize-learner"},
                    {"file": "/etc/maker-guide/config.toml"},
                    {"file": "/var/lib/maker-guide/state.db"},
                ]
            },
        ]
    }
    refresh = _state_arguments(
        state["roles::kam_classroom::bot::refresh_learner_routes"], "cmd.run"
    )
    assert refresh["name"] == "/usr/local/sbin/refresh-learner-routes"
    assert refresh["stateful"] is True
    assert not {"onchanges", "onlyif", "unless"} & refresh.keys()
    assert refresh["require"] == [
        {"cmd": "roles::kam_classroom::bot::database_migrate"},
        {"file": "/usr/local/bin/maker-guide-render-learner-routes"},
        {"file": "/usr/local/sbin/refresh-learner-routes"},
        {"service": "kam-classroom::caddy::service"},
        {"cmd": "kam-classroom::caddy::admin_ready"},
        {"service": "sssd::service"},
        {"cmd": "roles::kam_classroom::bot::initialize_participant::pmuller"},
        {"cmd": "roles::kam_classroom::bot::initialize_participant::wanlong"},
    ]
    assert state["roles::kam_classroom::bot::create_directories"] == {
        "file.directory": [
            {"name": "/run/maker-guide"},
            {"user": "maker-guide"},
            {"group": "humans"},
            {"mode": "2750"},
            {
                "require": [
                    {"file": "/etc/tmpfiles.d/maker-guide.conf"},
                    {"user": "roles::kam_classroom::bot::user"},
                    {"service": "sssd::service"},
                ]
            },
        ]
    }
    assert state["/etc/systemd/system/maker-guide-bot.service"] == {
        "file.managed": [
            {
                "source": "salt://roles/kam-classroom/templates/maker-guide-bot.service.j2"
            },
            {"template": "jinja"},
            {"user": "root"},
            {"group": "root"},
            {"mode": "0644"},
            {
                "context": {
                    "daemon_user": "maker-guide",
                    "daemon_group": "maker-guide",
                    "runtime_group": "humans",
                    "config_path": "/etc/maker-guide/config.toml",
                }
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::publish_release"},
                    {"file": "/usr/local/bin/maker-guide-bot"},
                    {"file": "/etc/maker-guide/config.toml"},
                ]
            },
        ]
    }
    assert state["/etc/systemd/system/maker-guide-sync-derived-data.service"] == {
        "file.managed": [
            {
                "source": (
                    "salt://roles/kam-classroom/templates/"
                    "maker-guide-sync-derived-data.service.j2"
                )
            },
            {"template": "jinja"},
            {"user": "root"},
            {"group": "root"},
            {"mode": "0644"},
            {
                "context": {
                    "daemon_user": "maker-guide",
                    "daemon_group": "maker-guide",
                    "runtime_group": "humans",
                    "config_path": "/etc/maker-guide/config.toml",
                    "makers_root": "/makers",
                    "documents_root": "/docs",
                }
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::publish_release"},
                    {"file": "/usr/local/bin/maker-guide-sync-derived-data"},
                    {"file": "/etc/maker-guide/config.toml"},
                    {"file": "/makers"},
                    {"file": "/docs"},
                ]
            },
        ]
    }
    assert state["/etc/systemd/system/maker-guide-sync-derived-data.timer"] == {
        "file.managed": [
            {
                "source": (
                    "salt://roles/kam-classroom/templates/"
                    "maker-guide-sync-derived-data.timer.j2"
                )
            },
            {"template": "jinja"},
            {"user": "root"},
            {"group": "root"},
            {"mode": "0644"},
            {"context": {"on_boot": "1m", "on_unit_active": "1m", "accuracy": "30s"}},
            {
                "require": [
                    {
                        "file": (
                            "/etc/systemd/system/maker-guide-sync-derived-data.service"
                        )
                    }
                ]
            },
        ]
    }
    assert state["/etc/systemd/system/maker-guide-build-docs.service"] == {
        "file.managed": [
            {
                "source": (
                    "salt://roles/kam-classroom/templates/"
                    "maker-guide-build-docs.service.j2"
                )
            },
            {"template": "jinja"},
            {"user": "root"},
            {"group": "root"},
            {"mode": "0644"},
            {
                "context": {
                    "daemon_user": "maker-guide",
                    "daemon_group": "maker-guide",
                    "runtime_group": "humans",
                    "config_path": "/etc/maker-guide/config.toml",
                    "makers_root": "/makers",
                    "docs_site_directory": "/var/www/maker-guide-docs",
                    "docs_site_output": "/var/www/maker-guide-docs/current",
                }
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::publish_release"},
                    {"file": "/usr/local/bin/maker-guide-build-docs"},
                    {"file": "/etc/maker-guide/config.toml"},
                    {"file": "/makers"},
                    {"file": "/var/www/maker-guide-docs"},
                    {"file": "/var/www/maker-guide-docs/current"},
                ]
            },
        ]
    }
    assert state["/etc/systemd/system/maker-guide-build-docs.timer"] == {
        "file.managed": [
            {
                "source": (
                    "salt://roles/kam-classroom/templates/maker-guide-build-docs.timer"
                )
            },
            {"user": "root"},
            {"group": "root"},
            {"mode": "0644"},
            {
                "require": [
                    {"file": "/etc/systemd/system/maker-guide-build-docs.service"}
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::systemd_reload"] == {
        "module.run": [
            {"service.systemctl_reload": []},
            {
                "onchanges": [
                    {"file": "/etc/systemd/system/maker-guide-bot.service"},
                    {
                        "file": (
                            "/etc/systemd/system/maker-guide-sync-derived-data.service"
                        )
                    },
                    {
                        "file": (
                            "/etc/systemd/system/maker-guide-sync-derived-data.timer"
                        )
                    },
                    {"file": "/etc/systemd/system/maker-guide-build-docs.service"},
                    {"file": "/etc/systemd/system/maker-guide-build-docs.timer"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::sync_derived_data"] == {
        "cmd.run": [
            {"name": "systemctl start maker-guide-sync-derived-data.service"},
            {
                "onchanges": [
                    {"file": "/makers"},
                    {"file": "/docs"},
                    {"cmd": "roles::kam_classroom::bot::publish_release"},
                    {"cmd": "roles::kam_classroom::bot::release_pending"},
                    {"file": "/etc/maker-guide/config.toml"},
                    {
                        "file": (
                            "/etc/systemd/system/maker-guide-sync-derived-data.service"
                        )
                    },
                ]
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::database_migrate"},
                    {"module": "roles::kam_classroom::bot::systemd_reload"},
                    {"file": "/makers"},
                    {"file": "/docs"},
                    {
                        "file": (
                            "/etc/systemd/system/maker-guide-sync-derived-data.service"
                        )
                    },
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::build_docs"] == {
        "cmd.run": [
            {"name": "systemctl start maker-guide-build-docs.service"},
            {
                "onchanges": [
                    {"cmd": "roles::kam_classroom::bot::publish_release"},
                    {"cmd": "roles::kam_classroom::bot::release_pending"},
                ]
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::database_migrate"},
                    {"module": "roles::kam_classroom::bot::systemd_reload"},
                    {"cmd": "roles::kam_classroom::bot::publish_release"},
                    {"file": "/etc/systemd/system/maker-guide-build-docs.service"},
                ]
            },
        ]
    }
    assert state["maker-guide-sync-derived-data.timer"] == {
        "service.running": [
            {"enable": True},
            {
                "require": [
                    {
                        "file": (
                            "/etc/systemd/system/maker-guide-sync-derived-data.service"
                        )
                    },
                    {
                        "file": (
                            "/etc/systemd/system/maker-guide-sync-derived-data.timer"
                        )
                    },
                    {"cmd": "roles::kam_classroom::bot::sync_derived_data"},
                    {"module": "roles::kam_classroom::bot::systemd_reload"},
                ]
            },
        ]
    }
    assert state["maker-guide-build-docs.timer"] == {
        "service.running": [
            {"enable": True},
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::database_migrate"},
                    {"file": "/etc/systemd/system/maker-guide-build-docs.service"},
                    {"file": "/etc/systemd/system/maker-guide-build-docs.timer"},
                    {"module": "roles::kam_classroom::bot::systemd_reload"},
                ]
            },
        ]
    }
    assert state["maker-guide-bot.service"] == {
        "service.running": [
            {"enable": True},
            {
                "watch": [
                    {"file": "/etc/systemd/system/maker-guide-bot.service"},
                    {"file": "/etc/maker-guide/config.toml"},
                    {"file": "/etc/maker-guide/secrets/irc-password"},
                    {"file": "/etc/maker-guide/secrets/openrouter-api-key"},
                    {"cmd": "roles::kam_classroom::bot::publish_release"},
                ]
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::database_migrate"},
                    {"file": "roles::kam_classroom::bot::create_directories"},
                    {"cmd": "dns-nftsets::service"},
                    {
                        "dns_nftsets": (
                            "roles::kam_classroom::bot::openrouter_dns_nftsets"
                        )
                    },
                    {"nftables_file": "roles::kam_classroom::bot::openrouter_egress"},
                    {"module": "roles::kam_classroom::bot::systemd_reload"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::verify_active_release"] == {
        "cmd.run": [
            {"name": "systemctl is-active --quiet maker-guide-bot.service"},
            {
                "onchanges": [
                    {"cmd": "roles::kam_classroom::bot::publish_release"},
                    {"cmd": "roles::kam_classroom::bot::release_pending"},
                    {"service": "maker-guide-bot.service"},
                ]
            },
            {"require": [{"service": "maker-guide-bot.service"}]},
        ]
    }
    assert state["roles::kam_classroom::bot::restore_registration"] == {
        "cmd.run": [
            {
                "name": (
                    "/usr/local/sbin/maker-guide-release "
                    "/usr/local/lib/maker-guide/incoming "
                    "/usr/local/lib/maker-guide/releases restore-registration"
                )
            },
            {
                "onlyif": (
                    "test -e "
                    "/usr/local/lib/maker-guide/registration-open.before-release"
                )
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::identity::lingering"},
                    {"cmd": "roles::kam_classroom::bot::database_migrate"},
                    {"cmd": "roles::kam_classroom::bot::verify_active_release"},
                    {"cmd": "roles::kam_classroom::bot::prune_releases"},
                    {"service": "maker-guide-bot.service"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::prune_releases"] == {
        "cmd.run": [
            {
                "name": (
                    "/usr/local/sbin/maker-guide-release "
                    "/usr/local/lib/maker-guide/incoming "
                    "/usr/local/lib/maker-guide/releases prune"
                )
            },
            {
                "onchanges": [
                    {"cmd": "roles::kam_classroom::bot::verify_active_release"}
                ]
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::verify_active_release"},
                    {"cmd": "roles::kam_classroom::bot::build_docs"},
                    {"cmd": "roles::kam_classroom::bot::refresh_learner_routes"},
                    {"cmd": "roles::kam_classroom::bot::sync_derived_data"},
                    {"file": "/usr/local/sbin/maker-guide-release"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::complete_release"] == {
        "cmd.run": [
            {
                "name": (
                    "/usr/local/sbin/maker-guide-release "
                    "/usr/local/lib/maker-guide/incoming "
                    "/usr/local/lib/maker-guide/releases complete"
                )
            },
            {"onchanges": [{"cmd": "roles::kam_classroom::bot::prune_releases"}]},
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::prune_releases"},
                    {"cmd": "roles::kam_classroom::bot::restore_registration"},
                ]
            },
        ]
    }


def test_role_bot_initializes_course_participants() -> None:
    """Test that all course participants receive the appropriate rank setting."""
    pillar = _kam_classroom_pillar()
    classroom = cast(dict[str, object], pillar["kam_classroom"])
    identity = cast(dict[str, object], classroom["identity"])
    identity["managed_users"] = {
        "volunteer": {
            "uid_number": 10011,
            "primary_group": "humans",
            "secondary_groups": ["volunteers", "linux-foundations"],
        },
        "student": {
            "uid_number": 10012,
            "primary_group": "humans",
            "secondary_groups": ["students", "linux-foundations"],
        },
    }

    state = _load_state("roles/kam-classroom/bot.sls", pillar)

    assert state["roles::kam_classroom::bot::initialize_participant::volunteer"] == {
        "cmd.run": [
            {
                "name": (
                    '/usr/local/bin/maker-guide-initialize-learner "volunteer" --uid '
                    '10011 --enroll --not-rank-eligible --config "/etc/maker-guide/config.toml"'
                )
            },
            {"runas": "maker-guide"},
            {
                "unless": (
                    "/usr/bin/python3 -c 'import sqlite3,sys;sys.exit(sqlite3.connect("
                    'sys.argv[1]).execute( "select 1 from learners where handle = ?",'
                    '(sys.argv[2],)).fetchone() is None)\' "/var/lib/maker-guide/state.db" '
                    '"volunteer"'
                )
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::database_migrate"},
                    {"cmd": "roles::kam_classroom::lldap_user::volunteer"},
                    {"file": "/usr/local/bin/maker-guide-initialize-learner"},
                    {"file": "/etc/maker-guide/config.toml"},
                    {"file": "/var/lib/maker-guide/state.db"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::bot::initialize_participant::student"] == {
        "cmd.run": [
            {
                "name": (
                    '/usr/local/bin/maker-guide-initialize-learner "student" --uid 10012 '
                    '--enroll --config "/etc/maker-guide/config.toml"'
                )
            },
            {"runas": "maker-guide"},
            {
                "unless": (
                    "/usr/bin/python3 -c 'import sqlite3,sys;sys.exit(sqlite3.connect("
                    'sys.argv[1]).execute( "select 1 from learners where handle = ?",'
                    '(sys.argv[2],)).fetchone() is None)\' "/var/lib/maker-guide/state.db" '
                    '"student"'
                )
            },
            {
                "require": [
                    {"cmd": "roles::kam_classroom::bot::database_migrate"},
                    {"cmd": "roles::kam_classroom::lldap_user::student"},
                    {"file": "/usr/local/bin/maker-guide-initialize-learner"},
                    {"file": "/etc/maker-guide/config.toml"},
                    {"file": "/var/lib/maker-guide/state.db"},
                ]
            },
        ]
    }
    refresh = _state_arguments(
        state["roles::kam_classroom::bot::refresh_learner_routes"], "cmd.run"
    )
    assert {
        requirement["cmd"]
        for requirement in cast(list[dict[str, str]], refresh["require"])
        if requirement.get("cmd", "").startswith(
            "roles::kam_classroom::bot::initialize_participant::"
        )
    } == {
        "roles::kam_classroom::bot::initialize_participant::volunteer",
        "roles::kam_classroom::bot::initialize_participant::student",
    }


def test_role_bot_enables_openrouter_when_api_key_is_configured() -> None:
    """Test that the bot receives OpenRouter credentials through a private key file."""
    pillar = _kam_classroom_pillar()
    pillar["ergo"] = {
        "server": {"name": "irc.kolamayermakers.org"},
        "channels": {"managed": ["#kolamayermakers", "#lf2607"]},
    }

    state = _load_state("roles/kam-classroom/bot.sls", pillar)

    assert state["/etc/maker-guide/secrets/openrouter-api-key"] == {
        "file.managed": [
            {"user": "root"},
            {"group": "maker-guide"},
            {"mode": "0640"},
            {"contents": "sk-or-test\n"},
            {"require": [{"file": "roles::kam_classroom::bot::secrets_directory"}]},
        ]
    }
    config_state = cast(
        dict[str, object],
        state["/etc/maker-guide/config.toml"],
    )
    config_entries = cast(list[object], config_state["file.managed"])
    assert config_entries[5] == {
        "context": {
            "socket_path": "/run/maker-guide/preexec.sock",
            "runtime_group": "humans",
            "database_path": "/var/lib/maker-guide/state.db",
            "irc_server": "irc.kolamayermakers.org",
            "irc_channels": ["#lf2607"],
            "irc_password_file": "/etc/maker-guide/secrets/irc-password",
            "irc_account": "guide",
            "llm_tutor_enabled": True,
        }
    }


def test_role_bot_config_uses_irc_account_as_nickname() -> None:
    """Test that the bot nickname satisfies Ergo's nick-equals-account policy."""
    config = cast(
        dict[str, object],
        tomllib.loads(
            _environment()
            .get_template("roles/kam-classroom/templates/maker-guide-config.toml.j2")
            .render(
                socket_path="/run/maker-guide/preexec.sock",
                runtime_group="humans",
                database_path="/var/lib/maker-guide/state.db",
                irc_server="irc.kolamayermakers.org",
                irc_channels=["#lf2607"],
                irc_password_file="/etc/maker-guide/secrets/irc-password",
                irc_account="guide",
                llm_tutor_enabled=True,
            )
        ),
    )
    irc = cast(dict[str, object], config["irc"])
    sasl = cast(dict[str, object], irc["sasl"])

    assert irc["nickname"] == "guide"
    assert irc["username"] == "guide"
    assert sasl["username"] == "guide"


def test_role_backup_requires_sqlite() -> None:
    """Test that backup waits for SQLite."""
    state = _load_state("roles/kam-classroom/backup.sls", _kam_classroom_pillar())

    assert cast(
        list[object],
        cast(dict[str, object], state["/usr/local/sbin/classroom-backup"])[
            "file.managed"
        ],
    )[-1] == {"require": [{"pkg": "roles::kam_classroom::sqlite3"}]}


def test_role_npm_egress_limits_learners_to_the_npm_registry() -> None:
    """Test that learner npm installs can reach only the registry over HTTPS."""
    assert _load_state("roles/kam-classroom/npm.sls", _kam_classroom_pillar()) == {
        "include": [
            "roles.kam-classroom.bot",
            "dns-nftsets.configuration",
            "dns-nftsets.service",
            "nftables",
        ],
        "roles::kam_classroom::npm::required_pillar": {
            "test.check_pillar": [
                {
                    "string": [
                        "dns-nftsets:configuration:path",
                        "dns-nftsets:configuration:set_timeout",
                        "kam_classroom:npm_egress:nftables_file",
                        "kam_classroom:npm_egress:header",
                        "kam_classroom:npm_egress:destination",
                        "kam_classroom:npm_egress:set_v4",
                        "kam_classroom:npm_egress:set_v6",
                        "kam_classroom:npm_egress:destination_position",
                        "kam_classroom:npm_egress:domain_position",
                        "kam_classroom:npm_egress:user",
                    ]
                },
                {
                    "integer": [
                        "kam_classroom:npm_egress:gid",
                        "kam_classroom:npm_egress:tcp_port",
                    ]
                },
                {"listing": ["kam_classroom:npm_egress:domains"]},
                {"failhard": True},
            ]
        },
        "roles::kam_classroom::npm::dns_nftsets": {
            "dns_nftsets.fragment": [
                {"target": "/etc/dns-nftsets/configuration.jsonl"},
                {"destination_position": 28},
                {"domain_position": 68},
                {
                    "destinations": {
                        "classroom-npm": {
                            "family": "inet",
                            "table": "filter",
                            "set_v4": "classroom_npm_v4",
                            "set_v6": "classroom_npm_v6",
                        }
                    }
                },
                {
                    "domains": [
                        {"exact": "registry.npmjs.org", "destination": "classroom-npm"}
                    ]
                },
                {"require_in": [{"concat": "dns-nftsets::configuration_file"}]},
                {"require": [{"test": "roles::kam_classroom::npm::required_pillar"}]},
            ]
        },
        "roles::kam_classroom::npm": {
            "nftables_file.managed": [
                {"name": "/etc/nftables.d/48-classroom-npm-egress.nft"},
                {"header": "# Classroom npm registry egress policy"},
                {"counters": ["output_classroom_npm"]},
                {
                    "sets": [
                        {
                            "name": "classroom_npm_v4",
                            "type": "ipv4_addr",
                            "flags": ["timeout"],
                            "timeout": "24h",
                            "position": "25",
                        },
                        {
                            "name": "classroom_npm_v6",
                            "type": "ipv6_addr",
                            "flags": ["timeout"],
                            "timeout": "24h",
                            "position": "25",
                        },
                    ]
                },
                {"chains": [{"name": "output", "position": "60"}]},
                {
                    "rules": [
                        {
                            "chain": "output",
                            "position": "10",
                            "rule": (
                                "meta skgid 1001 ip daddr @classroom_npm_v4 tcp dport 443 "
                                'counter name "output_classroom_npm" accept comment '
                                '"classroom npm registry"'
                            ),
                        },
                        {
                            "chain": "output",
                            "position": "11",
                            "rule": (
                                "meta skgid 1001 ip6 daddr @classroom_npm_v6 tcp dport 443 "
                                'counter name "output_classroom_npm" accept comment '
                                '"classroom npm registry"'
                            ),
                        },
                        {
                            "chain": "output",
                            "position": "12",
                            "rule": (
                                "meta skuid maker-guide ip daddr @classroom_npm_v4 tcp dport 443 "
                                'counter name "output_classroom_npm" accept comment '
                                '"classroom npm registry"'
                            ),
                        },
                        {
                            "chain": "output",
                            "position": "13",
                            "rule": (
                                "meta skuid maker-guide ip6 daddr @classroom_npm_v6 tcp dport 443 "
                                'counter name "output_classroom_npm" accept comment '
                                '"classroom npm registry"'
                            ),
                        },
                    ]
                },
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {
                    "require": [
                        {"file": "/etc/nftables.d"},
                        {"test": "roles::kam_classroom::npm::required_pillar"},
                        {"user": "roles::kam_classroom::bot::user"},
                    ]
                },
                {"require_in": [{"cmd": "dns-nftsets::service"}]},
                {"onchanges_in": [{"cmd": "nftables::reload"}]},
                {"watch_in": [{"cmd": "nftables::validate"}]},
            ]
        },
    }


def test_role_tldr_uses_shared_offline_cache() -> None:
    """Test that classroom tldr uses a shared prewarmed cache."""
    assert _load_state("roles/kam-classroom/tldr.sls", {}) == {
        "include": ["roles.kam-classroom.packages"],
        "/var/lib/tldr": {
            "file.directory": [
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {"makedirs": True},
            ]
        },
        "/var/lib/tldr/.tldrrc": {
            "file.managed": [
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {
                    "contents": (
                        "{\n"
                        '  "cache": "/var/cache/tldr",\n'
                        '  "platform": "linux",\n'
                        '  "skipUpdateWhenPageNotFound": true\n'
                        "}\n"
                    )
                },
                {"require": [{"file": "/var/lib/tldr"}]},
            ]
        },
        "/var/cache/tldr": {
            "file.directory": [
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {"makedirs": True},
            ]
        },
        "/usr/local/bin/tldr": {
            "file.managed": [
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {"follow_symlinks": False},
                {
                    "contents": (
                        "#!/bin/sh\n"
                        "export DOTENV_CONFIG_QUIET=true\n"
                        "unset NODE_OPTIONS\n"
                        "export HOME=/var/lib/tldr\n"
                        'exec /opt/packages/nodejs/bin/tldr "$@"\n'
                    )
                },
                {
                    "require": [
                        {"cmd": "nodejs::npm_global::tldr::install"},
                        {"file": "/var/lib/tldr/.tldrrc"},
                    ]
                },
            ]
        },
        "roles::kam_classroom::tldr::cache": {
            "cmd.run": [
                {
                    "name": (
                        "timeout 120s env HOME=/var/lib/tldr "
                        "DOTENV_CONFIG_QUIET=true /opt/packages/nodejs/bin/tldr "
                        "--update || true"
                    )
                },
                {"creates": "/var/cache/tldr/cache/shortIndex.json"},
                {
                    "require": [
                        {"cmd": "nodejs::npm_global::tldr::install"},
                        {"file": "/var/cache/tldr"},
                        {"file": "/var/lib/tldr/.tldrrc"},
                    ]
                },
            ]
        },
        "/etc/profile.d/dotenvx_quiet.sh": {
            "file.managed": [
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {"contents": "export DOTENV_CONFIG_QUIET=true"},
            ]
        },
    }


def test_role_logo_state_installs_toilet_lolcat_helper_and_motd_hook() -> None:
    """Test that the classroom logo helper has its terminal art dependencies."""
    assert _load_state("roles/kam-classroom/kolam-makers-logo.sls", {}) == {
        "include": ["bootstrap.packages"],
        "roles::kam_classroom::toilet": {
            "pkg.installed": [
                {"name": "toilet"},
                {
                    "require": [
                        {"module": "apt::refresh"},
                        {"test": "bootstrap::package_sources_ready"},
                    ]
                },
                {"require_in": [{"test": "bootstrap::apt_packages_ready"}]},
            ]
        },
        "roles::kam_classroom::lolcat": {
            "pkg.installed": [
                {"name": "lolcat"},
                {
                    "require": [
                        {"module": "apt::refresh"},
                        {"test": "bootstrap::package_sources_ready"},
                    ]
                },
                {"require_in": [{"test": "bootstrap::apt_packages_ready"}]},
            ]
        },
        "/usr/local/bin/kolam-makers-logo": {
            "file.managed": [
                {"source": "salt://roles/kam-classroom/files/kolam_makers_logo.sh"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {
                    "require": [
                        {"pkg": "roles::kam_classroom::toilet"},
                        {"pkg": "roles::kam_classroom::lolcat"},
                    ]
                },
            ]
        },
        "/etc/update-motd.d": {
            "file.directory": [
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
            ]
        },
        "/etc/update-motd.d/10-kolam-makers-logo": {
            "file.symlink": [
                {"target": "/usr/local/bin/kolam-makers-logo"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {"force": True},
                {
                    "require": [
                        {"file": "/usr/local/bin/kolam-makers-logo"},
                        {"file": "/etc/update-motd.d"},
                    ]
                },
            ]
        },
        "roles::kam_classroom::kolam_makers_logo::clear_stale_motd_cache": {
            "cmd.run": [
                {
                    "name": (
                        "rm -f /run/motd.dynamic && install -D -m 0644 "
                        "/usr/local/bin/kolam-makers-logo "
                        "/var/lib/kam-classroom/"
                        "kolam-makers-logo.motd-cache-version"
                    )
                },
                {
                    "unless": (
                        "cmp -s /usr/local/bin/kolam-makers-logo "
                        "/var/lib/kam-classroom/"
                        "kolam-makers-logo.motd-cache-version"
                    )
                },
                {
                    "require": [
                        {"file": "/usr/local/bin/kolam-makers-logo"},
                        {"file": "/etc/update-motd.d/10-kolam-makers-logo"},
                    ]
                },
            ]
        },
    }


def test_caddy_firewall_opens_http_and_https_input() -> None:
    """Test that the role opens Caddy HTTP and HTTPS ports."""
    assert _load_state("roles/kam-classroom/caddy/firewall.sls", _caddy_pillar()) == {
        "include": ["nftables"],
        "kam-classroom::caddy::firewall::required_pillar": {
            "test.check_pillar": [
                {"string": ["caddy:service_user"]},
                {"integer": ["caddy:http_port", "caddy:https_port"]},
                {"failhard": True},
            ]
        },
        "kam-classroom::caddy::firewall": {
            "nftables_file.managed": [
                {"name": "/etc/nftables.d/50-kam-classroom-caddy.nft"},
                {"header": "# Kolam Ayer Makers classroom Caddy HTTP and HTTPS policy"},
                {
                    "counters": [
                        "input_kam_classroom_caddy",
                        "output_kam_classroom_caddy_acme",
                    ]
                },
                {
                    "chains": [
                        {"name": "input", "position": "50"},
                        {"name": "output", "position": "50"},
                    ]
                },
                {
                    "rules": [
                        {
                            "chain": "input",
                            "position": "10",
                            "rule": (
                                "tcp dport { 80, 443 } counter name "
                                '"input_kam_classroom_caddy" accept comment '
                                '"kolam ayer makers classroom caddy http https"'
                            ),
                        },
                        {
                            "chain": "output",
                            "position": "10",
                            "rule": (
                                "meta skuid caddy tcp dport { 80, 443 } "
                                'counter name "output_kam_classroom_caddy_acme" '
                                'accept comment "kolam ayer makers classroom caddy acme"'
                            ),
                        },
                    ]
                },
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {
                    "require": [
                        {"file": "/etc/nftables.d"},
                        {"test": "kam-classroom::caddy::firewall::required_pillar"},
                    ]
                },
                {"watch_in": [{"cmd": "nftables::validate"}]},
            ]
        },
    }


def test_caddy_service_waits_for_nftables_reload() -> None:
    """Caddy starts after firewall, validation and systemd reload, then trusts its CA."""
    pillar = _caddy_pillar()
    cast(dict[str, object], pillar["caddy"])["local_certs"] = True
    state = _load_state("roles/kam-classroom/caddy/service.sls", pillar)
    service = _state_arguments(
        state["kam-classroom::caddy::service"], "service.running"
    )
    assert service["enable"] is True
    for requirement in (
        {"cmd": "nftables::reload"},
        {"cmd": "kam-classroom::caddy::configuration::validate"},
        {"module": "kam-classroom::caddy::daemon_reload"},
    ):
        assert requirement in cast(list[dict[str, str]], service["require"])
    assert {"file": "/etc/systemd/system/caddy.service.d/classroom.conf"} in cast(
        list[dict[str, str]], service["watch"]
    )
    assert _state_arguments(
        state["kam-classroom::caddy::daemon_reload"], "module.run"
    ) == {
        "service.systemctl_reload": [],
        "onchanges": [{"file": "/etc/systemd/system/caddy.service.d/classroom.conf"}],
    }
    guard = _state_arguments(
        state["kam-classroom::caddy::service::required_pillar"], "test.check_pillar"
    )
    assert {
        "caddy:admin_address",
        "caddy:runtime_directory",
        "caddy:runtime_directory_mode",
        "caddy:service_umask",
    } <= set(cast(list[str], guard["string"]))
    assert guard["failhard"] is True
    trust = _state_arguments(state["kam-classroom::caddy::local_ca_trusted"], "cmd.run")
    assert {"service": "kam-classroom::caddy::service"} in cast(
        list[dict[str, str]], trust["require"]
    )
    assert cast(str, trust["unless"]).startswith("cmp -s ")
    assert "update-ca-certificates" in cast(str, trust["name"])


@pytest.mark.parametrize(
    "socket_path", ["/run/caddy/admin.sock", "/run/caddy-test/admin.sock"]
)
def test_caddy_repairs_interrupted_admin_socket_migration(socket_path: str) -> None:
    """Missing sockets trigger recovery even when configuration files are unchanged."""
    pillar = _caddy_pillar()
    cast(dict[str, object], pillar["caddy"])["admin_address"] = f"unix/{socket_path}"
    recovery = _state_arguments(
        _load_state("roles/kam-classroom/caddy/service.sls", pillar)[
            "kam-classroom::caddy::admin_ready"
        ],
        "cmd.run",
    )
    assert recovery["name"] == (
        "/usr/bin/systemctl daemon-reload && /usr/bin/systemctl restart caddy"
    )
    assert shlex.split(cast(str, recovery["unless"])) == [
        "/usr/bin/test",
        "-S",
        socket_path,
    ]
    assert recovery["require"] == [{"service": "kam-classroom::caddy::service"}]
    assert not {"onchanges", "onlyif"} & recovery.keys()


def test_classroom_readiness_dependency_graph_is_acyclic() -> None:
    """Readiness edges order imports, services and users without an SSSD cycle."""
    pillar = _kam_classroom_pillar() | _caddy_pillar()
    pillar["sssd"] = _role_pillar("pillar/sssd.sls", "sssd", "production-host") | {
        "enabled": True
    }
    pillar["systemd"] = _role_pillar(
        "pillar/roles/kam-classroom/systemd.sls", "systemd", "production-host"
    )
    chunks: dict[tuple[str, str], dict[str, object]] = {}
    for template in (
        "roles/kam-classroom/caddy/config.sls",
        "roles/kam-classroom/caddy/service.sls",
        "roles/kam-classroom/bot.sls",
        "roles/kam-classroom/identity.sls",
        "sssd/service.sls",
        "systemd/drop_ins.sls",
    ):
        for identifier, body in _load_state(template, pillar).items():
            if identifier == "include":
                continue
            for function in cast(dict[str, object], body):
                state_type, function_name = function.split(".", 1)
                chunks[state_type, identifier] = {
                    "state": state_type,
                    "fun": function_name,
                    "__id__": identifier,
                    "__sls__": template,
                    "name": identifier,
                    **_state_arguments(body, function),
                }

    # ponytail: unrelated includes are leaves; use full highstate for cross-role cycles.
    for chunk in list(chunks.values()):
        for requisite in (
            "require",
            "watch",
            "onchanges",
            "require_in",
            "watch_in",
            "onchanges_in",
        ):
            for requirement in cast(list[dict[str, str]], chunk.get(requisite, [])):
                for state_type, identifier in requirement.items():
                    if (state_type, identifier) not in chunks:
                        chunks[state_type, identifier] = {
                            "state": state_type,
                            "fun": "nop",
                            "__id__": identifier,
                            "name": identifier,
                        }
    graph = DependencyGraph()
    for chunk in chunks.values():
        graph.add_chunk(chunk, allow_aggregate=False)
    for chunk in chunks.values():
        assert graph.add_requisites(chunk, []) is None
        for requisite in ("require_in", "watch_in", "onchanges_in"):
            for requirement in cast(list[dict[str, str]], chunk.get(requisite, [])):
                for state_type, identifier in requirement.items():
                    assert graph.add_dependency(
                        chunks[state_type, identifier],
                        RequisiteType(requisite.removesuffix("_in")),
                        cast(str, chunk["state"]),
                        cast(str, chunk["__id__"]),
                    )
    assert graph.find_cycle_edges() == []

    expected_dependencies = {
        ("cmd", "kam-classroom::caddy::configuration::validate"): {
            (RequisiteType.REQUIRE, "/etc/caddy/learner-routes.caddy"),
            (RequisiteType.ONCHANGES, "/etc/caddy/learner-routes.caddy"),
        },
        ("module", "kam-classroom::caddy::daemon_reload"): {
            (
                RequisiteType.ONCHANGES,
                "/etc/systemd/system/caddy.service.d/classroom.conf",
            ),
        },
        ("service", "kam-classroom::caddy::service"): {
            (RequisiteType.REQUIRE, "kam-classroom::caddy::configuration::validate"),
            (RequisiteType.REQUIRE, "kam-classroom::caddy::daemon_reload"),
        },
        ("cmd", "kam-classroom::caddy::admin_ready"): {
            (RequisiteType.REQUIRE, "kam-classroom::caddy::service"),
        },
        ("cmd", "roles::kam_classroom::bot::refresh_learner_routes"): {
            (RequisiteType.REQUIRE, "kam-classroom::caddy::service"),
            (RequisiteType.REQUIRE, "kam-classroom::caddy::admin_ready"),
            (RequisiteType.REQUIRE, "sssd::service"),
            (
                RequisiteType.REQUIRE,
                "roles::kam_classroom::bot::initialize_participant::pmuller",
            ),
            (
                RequisiteType.REQUIRE,
                "roles::kam_classroom::bot::initialize_participant::wanlong",
            ),
        },
        ("file", "/usr/local/sbin/lldap-delete-user"): {
            (RequisiteType.REQUIRE, "/usr/local/sbin/kam-classroom-lingering"),
        },
        ("file", "/usr/local/sbin/kam-classroom-lingering"): {
            (RequisiteType.REQUIRE, "/etc/kam-classroom-lingering.json"),
        },
        ("service", "sssd::service"): {
            (RequisiteType.REQUIRE, "roles::kam_classroom::sssd_uses_local_lldap"),
        },
        ("cmd", "roles::kam_classroom::identity::lingering"): {
            (RequisiteType.REQUIRE, "sssd::service"),
        },
        ("file", "/usr/local/bin/maker-guide-create-learner"): {
            (RequisiteType.REQUIRE, "roles::kam_classroom::identity::lingering"),
        },
        ("cmd", "roles::kam_classroom::bot::restore_registration"): {
            (RequisiteType.REQUIRE, "roles::kam_classroom::identity::lingering"),
        },
    }
    for key, expected in expected_dependencies.items():
        assert expected <= {
            (requisite_type, dependency["__id__"])
            for requisite_type, dependency in graph.get_dependencies(chunks[key])
        }


def test_role_data_root_is_traversable_by_services() -> None:
    """Test that the role owns the shared preserved data root."""
    assert _load_state("roles/kam-classroom/data.sls", {}) == {
        "/data": {
            "file.directory": [
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {"makedirs": True},
                {
                    "require_in": [
                        {"file": "forgejo::data_directory"},
                        {"file": "lldap::data_directory"},
                        {"file": "authelia::data_directory"},
                    ]
                },
            ]
        }
    }


def test_role_domain_pillar_defaults_to_production_domain() -> None:
    """Test that classroom service domains default to production."""
    assert _load_pillar_file("pillar/roles/kam-classroom/domain.sls") == {
        "kam_classroom": {
            "domain": {
                "public_domain": "kolamayermakers.org",
                "public_hostname": "lf2607.kolamayermakers.org",
            }
        }
    }


def test_role_domain_pillar_uses_dev_domain_for_lf_dev() -> None:
    """Test that the development classroom host uses the dev subdomain."""
    assert _load_pillar_file(
        "pillar/roles/kam-classroom/domain.sls",
        grains_id="kam-classroom-dev",
        deployment_environment="development",
    ) == {
        "kam_classroom": {
            "domain": {
                "public_domain": "dev.kolamayermakers.org",
                "public_hostname": "lf-dev.kolamayermakers.org",
            }
        }
    }


def test_role_hosts_maps_canonical_hostname_to_loopback() -> None:
    """Test Forgejo discovery reaches the local canonical HTTPS endpoint."""
    assert _load_state(
        "roles/kam-classroom/hosts.sls",
        {
            "kam_classroom": {
                "domain": {"public_hostname": "lf2607.kolamayermakers.org"}
            }
        },
    ) == {
        "roles::kam_classroom::hosts::required_pillar": {
            "test.check_pillar": [
                {"string": ["kam_classroom:domain:public_hostname"]},
                {"failhard": True},
            ]
        },
        "roles::kam_classroom::hosts::service_domains": {
            "host.present": [
                {"ip": "127.0.0.1"},
                {"names": ["lf2607.kolamayermakers.org"]},
                {"require": [{"test": "roles::kam_classroom::hosts::required_pillar"}]},
            ]
        },
    }


def test_role_caddy_pillar_disables_local_certs_by_default() -> None:
    """Test that production classroom hosts use public ACME certificates."""
    assert _load_pillar_file("pillar/roles/kam-classroom/caddy.sls") == {
        "caddy": {
            "domain": "lf2607.kolamayermakers.org",
            "docs_site_directory": "/var/www/maker-guide-docs/current",
            "learner_routes_file": "/etc/caddy/learner-routes.caddy",
            "local_certs": False,
        }
    }


def test_role_caddy_pillar_uses_public_certificates_for_lf_dev() -> None:
    """Test that the public development host uses ACME certificates."""
    assert _load_pillar_file(
        "pillar/roles/kam-classroom/caddy.sls",
        grains_id="kam-classroom-dev",
        deployment_environment="development",
    ) == {
        "caddy": {
            "domain": "lf-dev.kolamayermakers.org",
            "docs_site_directory": "/var/www/maker-guide-docs/current",
            "learner_routes_file": "/etc/caddy/learner-routes.caddy",
            "local_certs": False,
        }
    }


def test_role_authelia_pillar_uses_public_cookie_for_production() -> None:
    """Test that production Authelia serves the canonical domain only."""
    assert cast(
        dict[str, object],
        _role_pillar(
            "pillar/roles/kam-classroom/authelia.sls", "authelia", "production-host"
        )["session"],
    ) == {
        "cookies": [
            {
                "domain": "lf2607.kolamayermakers.org",
                "authelia_url": "https://lf2607.kolamayermakers.org/auth/",
            }
        ]
    }
    assert (
        cast(
            dict[str, object],
            _role_pillar(
                "pillar/roles/kam-classroom/authelia.sls", "authelia", "production-host"
            )["server"],
        )["path"]
        == "/auth"
    )


def test_role_authelia_pillar_uses_canonical_paths_for_lf_dev() -> None:
    """Test dev Authelia uses paths on the classroom host."""
    authelia = _role_pillar(
        "pillar/roles/kam-classroom/authelia.sls",
        "authelia",
        "kam-classroom-dev",
        "development",
    )
    identity_providers = cast(dict[str, object], authelia["identity_providers"])
    oidc = cast(dict[str, object], identity_providers["oidc"])
    clients = cast(list[dict[str, object]], oidc["clients"])

    assert cast(dict[str, object], authelia["session"]) == {
        "cookies": [
            {
                "domain": "lf-dev.kolamayermakers.org",
                "authelia_url": "https://lf-dev.kolamayermakers.org/auth/",
            },
        ]
    }
    assert cast(dict[str, object], authelia["access_control"])["rules"] == [
        {
            "domain": "lf-dev.kolamayermakers.org",
            "policy": "one_factor",
            "subject": "group:humans",
        },
    ]
    assert clients[0]["redirect_uris"] == [
        "https://lf-dev.kolamayermakers.org/git/user/oauth2/authelia/callback",
    ]
    assert clients[1]["redirect_uris"] == [
        "https://lf-dev.kolamayermakers.org/irc/",
    ]


def test_role_forgejo_pillar_skips_local_ca_requirement_for_production() -> None:
    """Test production Forgejo OIDC discovery does not require local CA trust."""
    assert _forgejo_authelia_require("production-host") == [
        {"host": "roles::kam_classroom::hosts::service_domains"},
        {"service": "authelia::service"},
        {"service": "kam-classroom::caddy::service"},
    ]


def test_role_forgejo_pillar_uses_public_caddy_for_lf_dev() -> None:
    """Test dev Forgejo OIDC discovery uses the public Caddy service."""
    assert _forgejo_authelia_require("kam-classroom-dev", "development") == [
        {"host": "roles::kam_classroom::hosts::service_domains"},
        {"service": "authelia::service"},
        {"service": "kam-classroom::caddy::service"},
    ]


def test_role_openssh_policy_allows_registration_and_ssh_noob_passwords() -> None:
    """Test that classroom SSH allows registration and noob password login."""
    assert _load_pillar_file("pillar/roles/kam-classroom/openssh-server.sls") == {
        "openssh-server": {
            "config": {
                "PasswordAuthentication": "no",
                "DebianBanner": "no",
                "KbdInteractiveAuthentication": "no",
                "ChallengeResponseAuthentication": "no",
                "AllowUsers": None,
                "AuthorizedKeysFile": ".ssh/authorized_keys",
                "AuthorizedKeysCommand": "/usr/bin/sss_ssh_authorizedkeys",
                "AuthorizedKeysCommandUser": "nobody",
                "PermitRootLogin": "prohibit-password",
                "ExposeAuthInfo": "yes",
                "PermitEmptyPasswords": "no",
                "PermitTTY": "yes",
                "DisableForwarding": "yes",
                "MaxAuthTries": 3,
                "LoginGraceTime": 20,
                "MaxStartups": "3:30:10",
                "MaxSessions": 2,
                "Match": [
                    {
                        "condition": "User new",
                        "options": {
                            "AuthenticationMethods": "none",
                            "PermitEmptyPasswords": "yes",
                            "PasswordAuthentication": "yes",
                            "ForceCommand": (
                                "/usr/bin/sudo "
                                "/usr/local/bin/maker-guide-registration check "
                                "&& exec "
                                "/usr/local/bin/maker-guide-register "
                                "--fully-qualified-domain-name lf2607.kolamayermakers.org "
                                "--login-host lf2607.kolamayermakers.org "
                                "--web-ssh-url https://lf2607.kolamayermakers.org/ssh/"
                            ),
                        },
                    },
                    {
                        "condition": "User git",
                        "options": {
                            "AuthorizedKeysFile": ("/data/forgejo/ssh/authorized_keys"),
                            "AuthenticationMethods": "publickey",
                        },
                    },
                    {
                        "condition": "Group linux-foundations",
                        "options": {
                            "AuthenticationMethods": "any",
                            "PasswordAuthentication": "yes",
                        },
                    },
                ],
            },
            "firewall": {
                "allowed_source_ipv4_prefixes": ["0.0.0.0/0"],
                "allowed_source_ipv6_prefixes": ["::/0"],
            },
        }
    }


def test_role_openssh_registration_uses_lf_dev_fqdn_login_host() -> None:
    """Test that dev registration prints the canonical SSH login FQDN."""
    pillar = cast(
        dict[str, object],
        _load_pillar_file(
            "pillar/roles/kam-classroom/openssh-server.sls",
            grains_id="kam-classroom-dev",
            deployment_environment="development",
        ),
    )
    openssh_server = cast(dict[str, object], pillar["openssh-server"])
    config = cast(dict[str, object], openssh_server["config"])
    match_rules = cast(list[dict[str, object]], config["Match"])
    new_user_options = cast(dict[str, object], match_rules[0]["options"])

    assert new_user_options["ForceCommand"] == (
        "/usr/bin/sudo "
        "/usr/local/bin/maker-guide-registration check "
        "&& exec "
        "/usr/local/bin/maker-guide-register "
        "--fully-qualified-domain-name lf-dev.kolamayermakers.org "
        "--login-host lf-dev.kolamayermakers.org "
        "--web-ssh-url https://lf-dev.kolamayermakers.org/ssh/"
    )


def test_role_ttyd_pillar_marks_web_registration_command() -> None:
    """Test that register.kolamayermakers.org marks registration as web-originated."""
    assert _load_pillar_file("pillar/roles/kam-classroom/ttyd.sls") == {
        "ttyd": {
            "web": {
                "assets": {
                    "route": "/ssh/ttyd-assets",
                    "directory": "/var/lib/ttyd/assets",
                    "favicon": {
                        "name": "terminal.svg",
                        "source": "salt://ttyd/files/terminal.svg",
                    },
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
                        },
                        {
                            "name": "HackNerdFontMono-Bold.ttf",
                            "url": (
                                "https://github.com/ryanoasis/nerd-fonts/raw/v3.4.0/"
                                "patched-fonts/Hack/Bold/HackNerdFontMono-Bold.ttf"
                            ),
                            "checksum": (
                                "sha256=711084fdea9f9eb4e5dbca372a19e6a5af996fc88bfce55918eeef560f0f6722"
                            ),
                            "family": "HackNerdFontMono",
                            "weight": 700,
                            "style": "normal",
                            "format": "truetype",
                        },
                        {
                            "name": "HackNerdFontMono-Italic.ttf",
                            "url": (
                                "https://github.com/ryanoasis/nerd-fonts/raw/v3.4.0/"
                                "patched-fonts/Hack/Italic/"
                                "HackNerdFontMono-Italic.ttf"
                            ),
                            "checksum": (
                                "sha256=86c6e1b14e2cb02ac8041269c53dac3673c70ff58375d1aafe0ecff8087f8126"
                            ),
                            "family": "HackNerdFontMono",
                            "weight": 400,
                            "style": "italic",
                            "format": "truetype",
                        },
                        {
                            "name": "HackNerdFontMono-BoldItalic.ttf",
                            "url": (
                                "https://github.com/ryanoasis/nerd-fonts/raw/v3.4.0/"
                                "patched-fonts/Hack/BoldItalic/"
                                "HackNerdFontMono-BoldItalic.ttf"
                            ),
                            "checksum": (
                                "sha256=82fca6ff9e87bc65b6abb1bbde1e3884fa9418bfb14f15b9db2d3274b87bf44e"
                            ),
                            "family": "HackNerdFontMono",
                            "weight": 700,
                            "style": "italic",
                            "format": "truetype",
                        },
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
                        "-o StrictHostKeyChecking=no "
                        "-o UserKnownHostsFile=/dev/null -o LogLevel=ERROR "
                        "new@localhost"
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


def test_identity_state_owns_lldap_sssd_and_user_helper() -> None:
    """Test that identity integration owns LLDAP, SSSD, and account tooling."""
    state = _load_state("roles/kam-classroom/identity.sls", _kam_classroom_pillar())

    assert state["include"] == [
        "quotas",
        "lldap",
        "forgejo.service",
        "pam-pwquality.package",
        "sssd",
        "systemd.drop_ins",
    ]
    guard_arguments = cast(
        dict[str, list[dict[str, object]]],
        state["roles::kam_classroom::identity::required_pillar"],
    )["test.check_pillar"]
    assert sum("listing" in argument for argument in guard_arguments) == 1
    guard = _state_arguments(
        state["roles::kam_classroom::identity::required_pillar"], "test.check_pillar"
    )
    assert guard["listing"] == [
        "kam_classroom:identity:lingering:packages",
        "kam_classroom:identity:managed_users:pmuller:secondary_groups",
        "kam_classroom:identity:managed_users:pmuller:ssh_public_keys",
        "kam_classroom:identity:managed_users:wanlong:secondary_groups",
        "kam_classroom:identity:managed_users:wanlong:ssh_public_keys",
        "kam_classroom:identity:managed_users:guide:secondary_groups",
    ]
    assert "kam_classroom:identity:lingering:group" in cast(list[str], guard["string"])
    assert "kam_classroom:identity:lingering" in cast(list[str], guard["dictionary"])
    assert {
        "kam_classroom:identity:lingering:uid_minimum",
        "kam_classroom:identity:lingering:uid_maximum",
    } <= set(cast(list[str], guard["integer"]))
    assert guard["failhard"] is True
    policy = _state_arguments(
        state["/etc/kam-classroom-lingering.json"], "file.managed"
    )
    assert json.loads(cast(str, policy["contents"])) == {
        "group": "linux-foundations",
        "uid_minimum": 10000,
        "uid_maximum": 20999,
    }
    assert (policy["user"], policy["group"], policy["mode"]) == ("root", "root", "0600")
    helper = _state_arguments(
        state["/usr/local/sbin/kam-classroom-lingering"], "file.managed"
    )
    assert (helper["user"], helper["group"], helper["mode"]) == ("root", "root", "0700")
    assert helper["require"] == [{"file": "/etc/kam-classroom-lingering.json"}]
    lingering = _state_arguments(
        state["roles::kam_classroom::identity::lingering"], "cmd.run"
    )
    assert lingering["name"] == "/usr/local/sbin/kam-classroom-lingering"
    assert lingering["stateful"] is True
    assert not {"onchanges", "onlyif", "unless"} & lingering.keys()
    for requirement in (
        {"test": "roles::kam_classroom::identity::required_pillar"},
        {"file": "/usr/local/sbin/kam-classroom-lingering"},
        {"service": "sssd::service"},
        {"service": "systemd::drop_ins::session_policy::service"},
        {"module": "systemd::drop_ins::resource_limits::daemon_reload"},
        {"cmd": "roles::kam_classroom::lldap_group::linux-foundations"},
        {"cmd": "roles::kam_classroom::lldap_group_migration::lf2607"},
        *(
            {"cmd": f"roles::kam_classroom::lldap_user::{username}"}
            for username in ("pmuller", "wanlong", "guide")
        ),
    ):
        assert requirement in cast(list[dict[str, str]], lingering["require"])
    for package in ("libpam-systemd", "dbus-user-session"):
        assert {"pkg": package} in cast(list[dict[str, str]], lingering["require"])
        installed = _state_arguments(state[package], "pkg.installed")
        assert installed["name"] == package
        assert {"test": "roles::kam_classroom::identity::required_pillar"} in cast(
            list[dict[str, str]], installed["require"]
        )
        assert installed["require_in"] == [{"test": "bootstrap::apt_packages_ready"}]
    assert {"file": "/usr/local/sbin/kam-classroom-lingering"} in cast(
        list[dict[str, str]],
        _state_arguments(state["/usr/local/sbin/lldap-delete-user"], "file.managed")[
            "require"
        ],
    )
    assert state["roles::kam_classroom::registration_group"] == {
        "group.present": [
            {"name": "new"},
            {"system": True},
            {"gid": 980},
        ]
    }
    assert state["roles::kam_classroom::registration_user"] == {
        "user.present": [
            {"name": "new"},
            {"uid": 986},
            {"gid": "new"},
            {"home": "/var/empty/kam-registration"},
            {"shell": "/bin/sh"},
            {"createhome": False},
            {"password": ""},
            {"enforce_password": True},
            {"password_lock": False},
            {"system": True},
            {
                "require": [
                    {"group": "roles::kam_classroom::registration_group"},
                    {"file": "roles::kam_classroom::registration_home"},
                ]
            },
        ]
    }
    assert set(
        cast(
            str,
            cast(
                dict[str, list[dict[str, object]]],
                state["/etc/sudoers.d/kam-registration"],
            )["file.managed"][4]["contents"],
        ).splitlines()
    ) == {
        "pmuller ALL=(root) NOPASSWD: "
        "/usr/local/bin/maker-guide-registration open, "
        "/usr/local/bin/maker-guide-registration close, "
        "/usr/local/bin/maker-guide-registration status",
        "new ALL=(root) NOPASSWD: /usr/local/bin/maker-guide-registration check",
        "new ALL=(root) NOPASSWD: /usr/local/bin/maker-guide-create-learner "
        "^--registration-mode [^ /]+ --email [^ ]+ --password-stdin$",
        "%mentors ALL=(maker-guide) NOPASSWD: "
        "/usr/local/bin/maker-guide-progress "
        "^release S(0[1-9]|[1-9][0-9]*) --source mentor$",
        "maker-guide ALL=(root) NOPASSWD: "
        "/usr/bin/systemctl start maker-guide-build-docs.service",
        "%mentors ALL=(root) NOPASSWD: "
        "/usr/local/bin/maker-guide-registration open, "
        "/usr/local/bin/maker-guide-registration close, "
        "/usr/local/bin/maker-guide-registration status",
    }
    assert state["/usr/local/sbin/lldap-ensure-user"] == {
        "file.managed": [
            {"source": "salt://roles/kam-classroom/files/lldap_ensure_user.py"},
            {"user": "root"},
            {"group": "root"},
            {"mode": "0750"},
            {
                "require": [
                    {"file": "lldap::secret_environment_file"},
                    {"service": "lldap::service"},
                    {"test": "roles::kam_classroom::identity::required_pillar"},
                ]
            },
        ]
    }
    assert state["/usr/local/sbin/lldap_ensure_user.py"] == {
        "file.managed": [
            {"source": "salt://roles/kam-classroom/files/lldap_ensure_user.py"},
            {"user": "root"},
            {"group": "root"},
            {"mode": "0644"},
            {"require": [{"file": "/usr/local/sbin/lldap-ensure-user"}]},
        ]
    }
    assert state["/usr/local/sbin/lldap-migrate-group-members"] == {
        "file.managed": [
            {
                "source": (
                    "salt://roles/kam-classroom/files/lldap_migrate_group_members.py"
                )
            },
            {"user": "root"},
            {"group": "root"},
            {"mode": "0750"},
            {
                "require": [
                    {"file": "/usr/local/sbin/lldap-ensure-user"},
                    {"file": "/usr/local/sbin/lldap_ensure_user.py"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::lldap_group_migration::lf2607"] == {
        "cmd.run": [
            {
                "name": (
                    "/usr/local/sbin/lldap-migrate-group-members lf2607 "
                    "linux-foundations"
                )
            },
            {
                "unless": (
                    "/usr/local/sbin/lldap-migrate-group-members lf2607 "
                    "linux-foundations --check"
                )
            },
            {
                "require": [
                    {"file": "/usr/local/sbin/lldap-migrate-group-members"},
                    {"cmd": "roles::kam_classroom::lldap_group::lf2607"},
                    {"cmd": ("roles::kam_classroom::lldap_group::linux-foundations")},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::lldap_user::pmuller"] == {
        "cmd.run": [
            {
                "name": (
                    '/usr/local/sbin/lldap-ensure-user "pmuller" '
                    '--uid-number 10009 --display-name "Philippe Muller" '
                    '--email "philippe.muller@kam-classroom-dev" '
                    '--home-directory "/home/pmuller" --shell "/bin/bash" '
                    '--primary-group "humans" --secondary-group "mentors" '
                    '--secondary-group "admins" --secondary-group "linux-foundations" '
                    "--ssh-public-key "
                    '"ssh-rsa AAAATEST cardno:25_939_134"'
                )
            },
            {
                "unless": (
                    '/usr/local/sbin/lldap-ensure-user "pmuller" '
                    '--uid-number 10009 --display-name "Philippe Muller" '
                    '--email "philippe.muller@kam-classroom-dev" '
                    '--home-directory "/home/pmuller" --shell "/bin/bash" '
                    '--primary-group "humans" --secondary-group "mentors" '
                    '--secondary-group "admins" --secondary-group "linux-foundations" '
                    "--ssh-public-key "
                    '"ssh-rsa AAAATEST cardno:25_939_134" --check'
                )
            },
            {
                "require": [
                    {"file": "/usr/local/sbin/lldap-ensure-user"},
                    {"test": "roles::kam_classroom::identity::required_pillar"},
                    {"cmd": "roles::kam_classroom::lldap_group::humans"},
                    {"cmd": "roles::kam_classroom::lldap_group::mentors"},
                    {"cmd": "roles::kam_classroom::lldap_group::admins"},
                    {"cmd": "roles::kam_classroom::lldap_group::linux-foundations"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::lldap_user::wanlong"] == {
        "cmd.run": [
            {
                "name": (
                    '/usr/local/sbin/lldap-ensure-user "wanlong" --uid-number 10010 '
                    '--display-name "Wanlong" --email "liwanlong@protonmail.com" '
                    '--home-directory "/home/wanlong" --shell "/bin/bash" '
                    '--primary-group "humans" --secondary-group "mentors" '
                    '--secondary-group "linux-foundations" --ssh-public-key '
                    '"ssh-rsa AAAATEST wanlong"'
                )
            },
            {
                "unless": (
                    '/usr/local/sbin/lldap-ensure-user "wanlong" --uid-number 10010 '
                    '--display-name "Wanlong" --email "liwanlong@protonmail.com" '
                    '--home-directory "/home/wanlong" --shell "/bin/bash" '
                    '--primary-group "humans" --secondary-group "mentors" '
                    '--secondary-group "linux-foundations" --ssh-public-key '
                    '"ssh-rsa AAAATEST wanlong" --check'
                )
            },
            {
                "require": [
                    {"file": "/usr/local/sbin/lldap-ensure-user"},
                    {"test": "roles::kam_classroom::identity::required_pillar"},
                    {"cmd": "roles::kam_classroom::lldap_group::humans"},
                    {"cmd": "roles::kam_classroom::lldap_group::mentors"},
                    {"cmd": "roles::kam_classroom::lldap_group::linux-foundations"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::lldap_user::guide"] == {
        "cmd.run": [
            {
                "name": (
                    '/usr/local/sbin/lldap-ensure-user "guide" --uid-number 9000 '
                    '--display-name "TheGuide" --email "guide@kam-classroom-dev" '
                    '--home-directory "/var/lib/guide" '
                    '--shell "/usr/sbin/nologin" --primary-group "guide" '
                    '--secondary-group "irc-bots"'
                )
            },
            {
                "unless": (
                    '/usr/local/sbin/lldap-ensure-user "guide" --uid-number 9000 '
                    '--display-name "TheGuide" --email "guide@kam-classroom-dev" '
                    '--home-directory "/var/lib/guide" '
                    '--shell "/usr/sbin/nologin" --primary-group "guide" '
                    '--secondary-group "irc-bots" --check'
                )
            },
            {
                "require": [
                    {"file": "/usr/local/sbin/lldap-ensure-user"},
                    {"test": "roles::kam_classroom::identity::required_pillar"},
                    {"cmd": "roles::kam_classroom::lldap_group::guide"},
                    {"cmd": "roles::kam_classroom::lldap_group::irc-bots"},
                ]
            },
        ]
    }
    assert state["/usr/local/sbin/lldap-create-user"] == {
        "file.managed": [
            {"source": "salt://roles/kam-classroom/files/lldap_create_user.py"},
            {"user": "root"},
            {"group": "root"},
            {"mode": "0750"},
            {
                "require": [
                    {"pkg": "roles::kam_classroom::diceware"},
                    {"pkg": "pam-pwquality::packages"},
                    {"cmd": "roles::kam_classroom::lldap_group::humans"},
                    {"file": "lldap::secret_environment_file"},
                    {"service": "lldap::service"},
                    {"service": "forgejo::service"},
                    {"file": "/usr/local/sbin/apply-user-quotas"},
                ]
            },
        ]
    }
    assert state["/usr/local/sbin/lldap-set-password"] == {
        "file.managed": [
            {"source": "salt://roles/kam-classroom/files/lldap_set_password.py"},
            {"user": "root"},
            {"group": "root"},
            {"mode": "0750"},
            {
                "require": [
                    {"pkg": "roles::kam_classroom::diceware"},
                    {"pkg": "pam-pwquality::packages"},
                    {"file": "lldap::secret_environment_file"},
                    {"service": "lldap::service"},
                ]
            },
        ]
    }
    assert state["roles::kam_classroom::sssd_uses_local_lldap"] == {
        "test.nop": [
            {
                "require": [
                    {"service": "lldap::service"},
                    {"file": "/usr/local/sbin/lldap-create-user"},
                    {"file": "/usr/local/sbin/lldap-set-password"},
                    {"file": "/usr/local/sbin/lldap-delete-user"},
                    {"file": "/usr/local/sbin/lldap-ensure-user"},
                ]
            },
            {"require_in": [{"service": "sssd::service"}]},
        ]
    }
    assert {
        state_identifier
        for state_identifier in state
        if state_identifier.startswith("roles::kam_classroom::lldap_group::")
    } == {
        "roles::kam_classroom::lldap_group::humans",
        "roles::kam_classroom::lldap_group::makers",
        "roles::kam_classroom::lldap_group::architects",
        "roles::kam_classroom::lldap_group::speakers",
        "roles::kam_classroom::lldap_group::lf2607",
        "roles::kam_classroom::lldap_group::admins",
        "roles::kam_classroom::lldap_group::mentors",
        "roles::kam_classroom::lldap_group::pa",
        "roles::kam_classroom::lldap_group::volunteers",
        "roles::kam_classroom::lldap_group::linux-foundations",
        "roles::kam_classroom::lldap_group::students",
        "roles::kam_classroom::lldap_group::guide",
        "roles::kam_classroom::lldap_group::irc-bots",
    }


@pytest.mark.parametrize("group", ["mentors", "unmanaged"])
def test_identity_lingering_requires_a_managed_policy_group(group: str) -> None:
    """The configured group controls lingering and unknown groups fail closed."""
    pillar = _kam_classroom_pillar()
    cast(
        dict[str, object],
        _SaltNamespace(pillar).pillar_get("kam_classroom:identity:lingering"),
    )["group"] = group
    state = _load_state("roles/kam-classroom/identity.sls", pillar)
    policy = _state_arguments(
        state["/etc/kam-classroom-lingering.json"], "file.managed"
    )
    assert json.loads(cast(str, policy["contents"])) == {
        "group": group,
        "uid_minimum": 10000,
        "uid_maximum": 20999,
    }
    assert policy["require"] == [
        {"test": "roles::kam_classroom::identity::required_pillar"}
    ]
    assert {"cmd": f"roles::kam_classroom::lldap_group::{group}"} in cast(
        list[dict[str, str]],
        _state_arguments(state["roles::kam_classroom::identity::lingering"], "cmd.run")[
            "require"
        ],
    )
    if group == "unmanaged":
        assert (
            _state_arguments(
                state["roles::kam_classroom::identity::lingering_group_is_managed"],
                "test.fail_without_changes",
            )["failhard"]
            is True
        )
    else:
        assert "roles::kam_classroom::identity::lingering_group_is_managed" not in state


def test_caddyfile_uses_narrow_path_routes() -> None:
    """Narrow routes and service reload share a private Unix admin endpoint."""
    pillar = _caddy_pillar()
    cast(dict[str, object], pillar["caddy"])["local_certs"] = True
    state = _load_state("roles/kam-classroom/caddy/config.sls", pillar)
    configuration = _state_arguments(state["/etc/caddy/Caddyfile"], "file.managed")
    assert configuration["template"] == "jinja"
    rendered = (
        _environment()
        .get_template(cast(str, configuration["source"]).removeprefix("salt://"))
        .render(**cast(dict[str, object], configuration["context"]))
    )
    override = _state_arguments(
        _load_state("roles/kam-classroom/caddy/service.sls", pillar)[
            "/etc/systemd/system/caddy.service.d/classroom.conf"
        ],
        "file.managed",
    )
    assert override["template"] == "jinja"
    assert (override["user"], override["group"], override["mode"]) == (
        "root",
        "root",
        "0644",
    )
    assert override["makedirs"] is True
    service_lines = (
        _environment()
        .get_template(cast(str, override["source"]).removeprefix("salt://"))
        .render(**cast(dict[str, object], override["context"]))
        .splitlines()
    )
    assert {
        "RuntimeDirectory=caddy",
        "RuntimeDirectoryMode=0700",
        "UMask=0077",
        "ExecReload=",
    } <= set(service_lines)
    reload_command = shlex.split(
        next(
            line.removeprefix("ExecReload=")
            for line in service_lines
            if line.startswith("ExecReload=/")
        )
    )
    admin_address = next(
        line.strip().split()[1]
        for line in rendered.splitlines()
        if line.strip().startswith("admin ")
    )
    assert admin_address == "unix//run/caddy/admin.sock"
    assert reload_command == [
        "/usr/bin/caddy",
        "reload",
        "--config",
        "/etc/caddy/Caddyfile",
        "--address",
        admin_address,
    ]
    assert "import /etc/caddy/learner-routes.caddy" in rendered
    routes = _state_arguments(state["/etc/caddy/learner-routes.caddy"], "file.managed")
    assert routes["contents"] == "# No learner routes.\n"
    assert routes["replace"] is False
    validation = _state_arguments(
        state["kam-classroom::caddy::configuration::validate"], "cmd.run"
    )
    for requisite in ("require", "onchanges"):
        assert {"file": "/etc/caddy/learner-routes.caddy"} in cast(
            list[dict[str, str]], validation[requisite]
        )

    assert (
        "@user_home_redirect path_regexp user_home_redirect ^/~[a-z][a-z0-9_-]*$"
        in rendered
    )
    assert (
        "redir @user_home_redirect {http.request.uri.path}/?{http.request.uri.query} permanent"
        in rendered
    )
    assert (
        "@user_home path_regexp user_home ^/~(?P<username>[a-z][a-z0-9_-]*)/(?P<path>.*)$"
        in rendered
    )
    assert "handle /api/v1/* {\n        reverse_proxy 127.0.0.1:3000\n    }" in rendered
    assert (
        "handle_path /git/* {\n        reverse_proxy 127.0.0.1:3000\n    }" in rendered
    )


def test_caddyfile_omits_dev_service_aliases() -> None:
    """Test dev Caddy serves the canonical lf-dev host only."""
    rendered = str(
        _environment()
        .get_template("roles/kam-classroom/caddy/templates/Caddyfile.j2")
        .render(
            forgejo_server=_forgejo_server(),
            lldap_http=_lldap_http(),
            authelia_server=_authelia_server(),
            gamja_paths=_gamja_paths(),
            ergo_server=_ergo_server(),
            ergo_listeners=_ergo_listeners(),
            registration_ttyd_server=_ttyd_server(),
            ssh_ttyd_server=_ssh_ttyd_server(),
            ttyd_web_assets=_ttyd_web_assets(),
            caddy={
                **cast(dict[str, object], _caddy_pillar()["caddy"]),
                "local_certs": False,
                "domain": "lf-dev.kolamayermakers.org",
                "docs_site_directory": "/var/www/maker-guide-docs/current",
                "learner_routes_file": "/etc/caddy/learner-routes.caddy",
            },
        )
    )

    assert [
        line
        for line in rendered.splitlines()
        if line.startswith(("git", "lldap", "auth", "register", "ssh", "irc"))
    ] == []
    assert "lf-dev.kolamayermakers.org {" in rendered


def test_irc_state_synchronizes_ergo_certificate_idempotently() -> None:
    """Test classroom IRC integration low state."""
    assert _load_state("roles/kam-classroom/irc.sls", _irc_pillar()) == {
        "include": ["ergo.service", "gamja", "roles.kam-classroom.caddy", "nftables"],
        "roles::kam_classroom::irc::required_pillar": {
            "test.check_pillar": [
                {
                    "string": [
                        "ergo:service:user",
                        "ergo:service:group",
                        "ergo:paths:cert_sync_script",
                        "ergo:paths:cert_sync_service",
                        "ergo:paths:cert_sync_timer",
                        "ergo:paths:tls_directory",
                        "ergo:paths:certificate_file",
                        "ergo:paths:certificate_key_file",
                        "ergo:server:name",
                        "ergo:listeners:irc:address",
                    ]
                },
                {"failhard": True},
            ]
        },
        "/usr/local/sbin/ergo-sync-caddy-cert": {
            "file.managed": [
                {
                    "source": "salt://roles/kam-classroom/templates/ergo-sync-caddy-cert.sh.j2"
                },
                {"template": "jinja"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {
                    "context": {
                        "paths": {
                            "cert_sync_script": "/usr/local/sbin/ergo-sync-caddy-cert",
                            "cert_sync_service": "/etc/systemd/system/ergo-sync-caddy-cert.service",
                            "cert_sync_timer": "/etc/systemd/system/ergo-sync-caddy-cert.timer",
                            "tls_directory": "/etc/ergo/tls",
                            "certificate_file": "/etc/ergo/tls/fullchain.pem",
                            "certificate_key_file": "/etc/ergo/tls/privkey.pem",
                        },
                        "server": {"name": "irc.kolamayermakers.org"},
                        "service": {"user": "ergo", "group": "ergo"},
                    }
                },
                {"require": [{"test": "roles::kam_classroom::irc::required_pillar"}]},
            ]
        },
        "roles::kam_classroom::ergo_caddy_certificate_sync": {
            "cmd.run": [
                {
                    "name": (
                        "/usr/local/sbin/ergo-sync-caddy-cert --wait-seconds 120 "
                        "irc.kolamayermakers.org"
                    )
                },
                {
                    "unless": (
                        "/usr/local/sbin/ergo-sync-caddy-cert --check "
                        "irc.kolamayermakers.org"
                    )
                },
                {
                    "require": [
                        {"file": "/usr/local/sbin/ergo-sync-caddy-cert"},
                        {"service": "kam-classroom::caddy::service"},
                        {"file": "ergo::tls_directory"},
                        {"test": "roles::kam_classroom::irc::required_pillar"},
                    ]
                },
                {"require_in": [{"service": "ergo::service"}]},
                {"watch_in": [{"service": "ergo::service"}]},
            ]
        },
        "/etc/systemd/system/ergo-sync-caddy-cert.service": {
            "file.managed": [
                {
                    "source": (
                        "salt://roles/kam-classroom/templates/"
                        "ergo-sync-caddy-cert.service.j2"
                    )
                },
                {"template": "jinja"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {
                    "context": {
                        "paths": {
                            "cert_sync_script": "/usr/local/sbin/ergo-sync-caddy-cert",
                            "cert_sync_service": "/etc/systemd/system/ergo-sync-caddy-cert.service",
                            "cert_sync_timer": "/etc/systemd/system/ergo-sync-caddy-cert.timer",
                            "tls_directory": "/etc/ergo/tls",
                            "certificate_file": "/etc/ergo/tls/fullchain.pem",
                            "certificate_key_file": "/etc/ergo/tls/privkey.pem",
                        },
                        "server": {"name": "irc.kolamayermakers.org"},
                    }
                },
                {
                    "require": [
                        {"file": "/usr/local/sbin/ergo-sync-caddy-cert"},
                        {"test": "roles::kam_classroom::irc::required_pillar"},
                    ]
                },
            ]
        },
        "/etc/systemd/system/ergo-sync-caddy-cert.timer": {
            "file.managed": [
                {
                    "source": "salt://roles/kam-classroom/templates/ergo-sync-caddy-cert.timer.j2"
                },
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {"require": [{"test": "roles::kam_classroom::irc::required_pillar"}]},
            ]
        },
        "roles::kam_classroom::ergo_cert_sync_systemd_daemon_reload": {
            "module.run": [
                {"service.systemctl_reload": []},
                {
                    "onchanges": [
                        {"file": "/etc/systemd/system/ergo-sync-caddy-cert.service"},
                        {"file": "/etc/systemd/system/ergo-sync-caddy-cert.timer"},
                    ]
                },
            ]
        },
        "roles::kam_classroom::ergo_cert_sync_timer": {
            "service.running": [
                {"name": "ergo-sync-caddy-cert.timer"},
                {"enable": True},
                {
                    "require": [
                        {"file": "/etc/systemd/system/ergo-sync-caddy-cert.service"},
                        {"file": "/etc/systemd/system/ergo-sync-caddy-cert.timer"},
                        {
                            "module": (
                                "roles::kam_classroom::"
                                "ergo_cert_sync_systemd_daemon_reload"
                            )
                        },
                        {"test": "roles::kam_classroom::irc::required_pillar"},
                    ]
                },
            ]
        },
        "roles::kam_classroom::irc::firewall": {
            "nftables_file.managed": [
                {"name": "/etc/nftables.d/50-kam-classroom-irc.nft"},
                {"header": "# Kolam Ayer Makers classroom IRC TLS policy"},
                {"counters": ["input_irc_tls"]},
                {"chains": [{"name": "input", "position": "50"}]},
                {
                    "rules": [
                        {
                            "chain": "input",
                            "position": "20",
                            "rule": (
                                'tcp dport 6697 counter name "input_irc_tls" '
                                'accept comment "kolam ayer makers classroom irc tls"'
                            ),
                        }
                    ]
                },
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {
                    "require": [
                        {"file": "/etc/nftables.d"},
                        {"test": "roles::kam_classroom::irc::required_pillar"},
                    ]
                },
                {"watch_in": [{"cmd": "nftables::validate"}]},
            ]
        },
    }


def test_ergo_certificate_sync_check_mode_finds_local_caddy_certificate(
    tmp_path: Path,
) -> None:
    """Test the sync script supports Caddy's local certificate issuer."""
    domain = "irc.kolamayermakers.org"
    certificate_root = tmp_path / "caddy-certificates"
    caddy_certificate_directory = certificate_root / "local" / domain
    caddy_certificate_directory.mkdir(parents=True)
    _ = (caddy_certificate_directory / f"{domain}.crt").write_text(
        "certificate\n",
        encoding="utf-8",
    )
    _ = (caddy_certificate_directory / f"{domain}.key").write_text(
        "key\n",
        encoding="utf-8",
    )
    destination_certificate = tmp_path / "fullchain.pem"
    destination_key = tmp_path / "privkey.pem"
    _ = destination_certificate.write_text("certificate\n", encoding="utf-8")
    _ = destination_key.write_text("key\n", encoding="utf-8")
    script_path = tmp_path / "ergo-sync-caddy-cert"
    _ = script_path.write_text(
        _environment()
        .get_template("roles/kam-classroom/templates/ergo-sync-caddy-cert.sh.j2")
        .render(
            paths={
                "certificate_file": str(destination_certificate),
                "certificate_key_file": str(destination_key),
            },
            server={"name": domain},
            service={"user": "ergo", "group": "ergo"},
        ),
        encoding="utf-8",
    )
    script_path.chmod(0o755)
    script_command = [str(script_path), "--check", domain]
    script_environment = os.environ | {"CADDY_CERTIFICATES_ROOT": str(certificate_root)}

    assert subprocess.run(script_command, env=script_environment).returncode == 0

    _ = destination_certificate.write_text("different\n", encoding="utf-8")

    assert subprocess.run(script_command, env=script_environment).returncode == 1
