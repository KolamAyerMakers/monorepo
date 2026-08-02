"""Tests for Ergo states."""

from __future__ import annotations

import importlib
from typing import Protocol, TypeGuard, cast

from tests.support.paths import SALTSTACK_DIRECTORY


class _Template(Protocol):
    def render(self, **context: object) -> str:
        """Render template."""
        ...


class _Environment(Protocol):
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
        if key == "grains.get":
            return self.grains_get
        raise KeyError(key)

    def grains_get(self, key: str, default: object = None) -> object:
        """Return grain data for the requested key."""
        if key == "cpuarch":
            return "x86_64"
        return default

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


def _environment() -> _Environment:
    jinja2 = importlib.import_module("jinja2")
    environment_factory = cast(_EnvironmentFactory, getattr(jinja2, "Environment"))
    loader_factory = cast(_LoaderFactory, getattr(jinja2, "FileSystemLoader"))
    environment = environment_factory(
        loader=loader_factory(str(SALTSTACK_DIRECTORY / "states")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    cast(dict[str, object], getattr(environment, "filters"))["yaml"] = _yaml_filter
    return environment


def _load_state(template: str, pillar: dict[str, object]) -> dict[str, object]:
    yaml_module = cast(_YamlModule, cast(object, importlib.import_module("yaml")))
    return cast(
        dict[str, object],
        yaml_module.safe_load(
            _environment().get_template(template).render(salt=_SaltNamespace(pillar))
        ),
    )


def _load_yaml_template(template: str, context: dict[str, object]) -> dict[str, object]:
    yaml_module = cast(_YamlModule, cast(object, importlib.import_module("yaml")))
    return cast(
        dict[str, object],
        yaml_module.safe_load(_environment().get_template(template).render(**context)),
    )


def _pillar() -> dict[str, object]:
    return {
        "ergo": {
            "service": {
                "user": "ergo",
                "group": "ergo",
                "gid": 979,
                "shell": "/usr/sbin/nologin",
                "home": "/var/lib/ergo",
                "system_user": True,
                "create_home": False,
                "unit_file": "/etc/systemd/system/ergo.service",
            },
            "paths": {
                "configuration_directory": "/etc/ergo",
                "configuration_file": "/etc/ergo/ircd.yaml",
                "data_directory": "/data/ergo",
                "tls_directory": "/etc/ergo/tls",
                "certificate_file": "/etc/ergo/tls/fullchain.pem",
                "certificate_key_file": "/etc/ergo/tls/privkey.pem",
                "auth_script_file": "/usr/local/sbin/ergo-lldap-auth",
                "channel_script_file": "/usr/local/sbin/ergo-ensure-channel",
                "managed_channels_file": "/etc/ergo/managed-channels.json",
                "motd_file": "/etc/ergo/ergo.motd",
            },
            "network": {"name": "KolamAyerMakers"},
            "server": {
                "name": "irc.meh.gripe",
                "websocket_origin": "https://irc.meh.gripe",
                "lookup_hostnames": True,
                "forward_confirm_hostnames": True,
                "proxy_allowed_from": ["localhost"],
                "ip_cloaking": {
                    "enabled": False,
                    "enabled_for_always_on": True,
                    "netname": "kolamayermakers",
                    "cidr_len_ipv4": 32,
                    "cidr_len_ipv6": 64,
                    "num_bits": 64,
                },
            },
            "listeners": {
                "irc": {"address": ":6697"},
                "websocket": {"address": "127.0.0.1:8097"},
            },
            "auth": {
                "ldap_uri": "ldap://127.0.0.1:3890",
                "base_dn": "dc=kolamayermakers,dc=org",
                "required_group": "humans",
                "allowed_groups": ["humans", "irc-bots"],
            },
            "accounts": {
                "login_throttling": {
                    "enabled": True,
                    "duration": "1m",
                    "max_attempts": 3,
                }
            },
            "oauth2": {
                "enabled": True,
                "autocreate": True,
                "introspection_url": "https://auth.meh.gripe/api/oidc/introspection",
                "introspection_timeout": "10s",
                "client_id": "gamja",
            },
            "channels": {
                "auto_join": ["#kolamayermakers", "#lf2607"],
                "managed": [
                    {"name": "#kolamayermakers", "operators": ["pmuller"]},
                    {"name": "#lf2607", "operators": ["pmuller"]},
                ],
                "founder": "kolamayermakers",
            },
            "motd": {
                "source": "salt://roles/kam-classroom/files/ergo.motd",
                "contents": (
                    "\n"
                    " _  __    _              __  __      _\n"
                    "| |/ /___| |__ _ _ __   |  \\/  |__ _| |_____ _ _ ___\n"
                    "| ' </ _ \\ / _` | '  \\  | |\\/| / _` | / / -_) '_(_-<\n"
                    "|_|\\_\\___/_\\__,_|_|_|_| |_|  |_\\__,_|_\\_\\___|_| /__/\n"
                    "\n"
                    "             Build.  Break.  Repeat.\n"
                ),
            },
        }
    }


def test_ergo_package_installs_binary_and_auth_dependencies() -> None:
    """Test Ergo package state."""
    assert _load_state(
        "ergo/package.sls", {"packages": {"ergo": {"version": "2.18.0"}}}
    ) == {
        "include": ["github.download_egress"],
        "ergo::openssl": {
            "pkg.installed": [
                {"name": "openssl"},
                {
                    "require": [
                        {"module": "apt::refresh"},
                        {"test": "bootstrap::package_sources_ready"},
                    ]
                },
                {"require_in": [{"test": "bootstrap::apt_packages_ready"}]},
            ]
        },
        "ergo::ldap_utils": {
            "pkg.installed": [
                {"name": "ldap-utils"},
                {
                    "require": [
                        {"module": "apt::refresh"},
                        {"test": "bootstrap::package_sources_ready"},
                    ]
                },
                {"require_in": [{"test": "bootstrap::apt_packages_ready"}]},
            ]
        },
        "ergo": {
            "packages.binary_package": [
                {"name": "ergo"},
                {"strip_components": 1},
                {
                    "require": [
                        {"test": "bootstrap::package_sources_ready"},
                        {"test": "github::download_egress::ready"},
                    ]
                },
            ]
        },
        "ergo::languages_directory_compatibility_symlink": {
            "file.symlink": [
                {"name": "/opt/packages/ergo/languages"},
                {"target": "/opt/packages/ergo/ergo-2.18.0-linux-x86_64/languages"},
                {
                    "onlyif": (
                        "test ! -d /opt/packages/ergo/languages -a -d "
                        "/opt/packages/ergo/ergo-2.18.0-linux-x86_64/languages"
                    )
                },
                {"require": [{"packages": "ergo"}]},
            ]
        },
    }


def test_ergo_config_state_manages_private_irc_service() -> None:
    """Test Ergo low state for the classroom IRC service."""
    assert _load_state("ergo/config.sls", _pillar()) == {
        "include": ["ergo.package"],
        "ergo::configuration::required_pillar": {
            "test.check_pillar": [
                {
                    "string": [
                        "ergo:service:user",
                        "ergo:service:group",
                        "ergo:service:shell",
                        "ergo:service:home",
                        "ergo:service:unit_file",
                        "ergo:paths:configuration_directory",
                        "ergo:paths:configuration_file",
                        "ergo:paths:data_directory",
                        "ergo:paths:tls_directory",
                        "ergo:paths:certificate_file",
                        "ergo:paths:certificate_key_file",
                        "ergo:paths:auth_script_file",
                        "ergo:paths:channel_script_file",
                        "ergo:paths:managed_channels_file",
                        "ergo:paths:motd_file",
                        "ergo:network:name",
                        "ergo:server:name",
                        "ergo:server:websocket_origin",
                        "ergo:server:ip_cloaking:netname",
                        "ergo:listeners:irc:address",
                        "ergo:listeners:websocket:address",
                        "ergo:auth:ldap_uri",
                        "ergo:auth:base_dn",
                        "ergo:auth:required_group",
                        "ergo:accounts:login_throttling:duration",
                        "ergo:oauth2:introspection_timeout",
                        "ergo:motd:contents",
                    ]
                },
                {
                    "boolean": [
                        "ergo:service:system_user",
                        "ergo:service:create_home",
                        "ergo:oauth2:enabled",
                        "ergo:oauth2:autocreate",
                        "ergo:server:lookup_hostnames",
                        "ergo:server:forward_confirm_hostnames",
                        "ergo:server:ip_cloaking:enabled",
                        "ergo:server:ip_cloaking:enabled_for_always_on",
                        "ergo:accounts:login_throttling:enabled",
                    ]
                },
                {
                    "integer": [
                        "ergo:service:gid",
                        "ergo:accounts:login_throttling:max_attempts",
                    ]
                },
                {
                    "listing": [
                        "ergo:server:proxy_allowed_from",
                        "ergo:auth:allowed_groups",
                        "ergo:channels:auto_join",
                    ]
                },
                {"failhard": True},
            ]
        },
        "ergo::group": {
            "group.present": [
                {"name": "ergo"},
                {"system": True},
                {"gid": 979},
                {"require": [{"test": "ergo::configuration::required_pillar"}]},
            ]
        },
        "ergo::user": {
            "user.present": [
                {"name": "ergo"},
                {"system": True},
                {"shell": "/usr/sbin/nologin"},
                {"home": "/var/lib/ergo"},
                {"createhome": False},
                {"gid": "ergo"},
                {
                    "require": [
                        {"group": "ergo::group"},
                        {"test": "ergo::configuration::required_pillar"},
                    ]
                },
            ]
        },
        "ergo::configuration_directory": {
            "file.directory": [
                {"name": "/etc/ergo"},
                {"user": "root"},
                {"group": "ergo"},
                {"mode": "0750"},
                {
                    "require": [
                        {"user": "ergo::user"},
                        {"test": "ergo::configuration::required_pillar"},
                    ]
                },
            ]
        },
        "ergo::data_directory": {
            "file.directory": [
                {"name": "/data/ergo"},
                {"user": "ergo"},
                {"group": "ergo"},
                {"mode": "0750"},
                {"makedirs": True},
                {"recurse": ["user", "group"]},
                {
                    "require": [
                        {"user": "ergo::user"},
                        {"test": "ergo::configuration::required_pillar"},
                    ]
                },
            ]
        },
        "ergo::tls_directory": {
            "file.directory": [
                {"name": "/etc/ergo/tls"},
                {"user": "root"},
                {"group": "ergo"},
                {"mode": "0750"},
                {"makedirs": True},
                {
                    "require": [
                        {"user": "ergo::user"},
                        {"test": "ergo::configuration::required_pillar"},
                    ]
                },
            ]
        },
        "ergo::bootstrap_tls_certificate": {
            "cmd.run": [
                {
                    "name": (
                        "openssl req -x509 -nodes -newkey rsa:2048 "
                        "-keyout /etc/ergo/tls/privkey.pem "
                        "-out /etc/ergo/tls/fullchain.pem -days 7 "
                        "-subj /CN=irc.meh.gripe && chown root:ergo "
                        "/etc/ergo/tls/fullchain.pem /etc/ergo/tls/privkey.pem "
                        "&& chmod 0640 /etc/ergo/tls/fullchain.pem "
                        "/etc/ergo/tls/privkey.pem"
                    )
                },
                {
                    "unless": (
                        "test -s /etc/ergo/tls/fullchain.pem -a "
                        "-s /etc/ergo/tls/privkey.pem"
                    )
                },
                {
                    "require": [
                        {"pkg": "ergo::openssl"},
                        {"file": "ergo::tls_directory"},
                        {"test": "ergo::configuration::required_pillar"},
                    ]
                },
            ]
        },
        "/usr/local/sbin/ergo-lldap-auth": {
            "file.managed": [
                {"source": "salt://ergo/files/ergo_lldap_auth.py"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {
                    "require": [
                        {"pkg": "ergo::ldap_utils"},
                        {"test": "ergo::configuration::required_pillar"},
                    ]
                },
            ]
        },
        "/usr/local/sbin/ergo-ensure-channel": {
            "file.managed": [
                {"source": "salt://ergo/files/ergo_ensure_channel.py"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0755"},
                {
                    "require": [
                        {"test": "ergo::configuration::required_pillar"},
                    ]
                },
            ]
        },
        "/etc/ergo/managed-channels.json": {
            "file.serialize": [
                {"formatter": "json"},
                {
                    "dataset": [
                        {"name": "#kolamayermakers", "operators": ["pmuller"]},
                        {"name": "#lf2607", "operators": ["pmuller"]},
                    ]
                },
                {"user": "root"},
                {"group": "ergo"},
                {"mode": "0640"},
                {
                    "require": [
                        {"file": "ergo::configuration_directory"},
                        {"test": "ergo::configuration::required_pillar"},
                    ]
                },
            ]
        },
        "/etc/ergo/ergo.motd": {
            "file.managed": [
                {"user": "root"},
                {"group": "ergo"},
                {"mode": "0640"},
                {"source": "salt://roles/kam-classroom/files/ergo.motd"},
                {
                    "require": [
                        {"file": "ergo::configuration_directory"},
                        {"test": "ergo::configuration::required_pillar"},
                    ]
                },
            ]
        },
        "/etc/ergo/ircd.yaml": {
            "file.managed": [
                {"source": "salt://ergo/templates/ircd.yaml.j2"},
                {"template": "jinja"},
                {"user": "root"},
                {"group": "ergo"},
                {"mode": "0640"},
                {
                    "context": {
                        "paths": {
                            "configuration_directory": "/etc/ergo",
                            "configuration_file": "/etc/ergo/ircd.yaml",
                            "data_directory": "/data/ergo",
                            "tls_directory": "/etc/ergo/tls",
                            "certificate_file": "/etc/ergo/tls/fullchain.pem",
                            "certificate_key_file": "/etc/ergo/tls/privkey.pem",
                            "auth_script_file": "/usr/local/sbin/ergo-lldap-auth",
                            "channel_script_file": "/usr/local/sbin/ergo-ensure-channel",
                            "managed_channels_file": "/etc/ergo/managed-channels.json",
                            "motd_file": "/etc/ergo/ergo.motd",
                        },
                        "network": {"name": "KolamAyerMakers"},
                        "server": {
                            "name": "irc.meh.gripe",
                            "websocket_origin": "https://irc.meh.gripe",
                            "lookup_hostnames": True,
                            "forward_confirm_hostnames": True,
                            "proxy_allowed_from": ["localhost"],
                            "ip_cloaking": {
                                "enabled": False,
                                "enabled_for_always_on": True,
                                "netname": "kolamayermakers",
                                "cidr_len_ipv4": 32,
                                "cidr_len_ipv6": 64,
                                "num_bits": 64,
                            },
                        },
                        "listeners": {
                            "irc": {"address": ":6697"},
                            "websocket": {"address": "127.0.0.1:8097"},
                        },
                        "auth": {
                            "ldap_uri": "ldap://127.0.0.1:3890",
                            "base_dn": "dc=kolamayermakers,dc=org",
                            "required_group": "humans",
                            "allowed_groups": ["humans", "irc-bots"],
                        },
                        "accounts": {
                            "login_throttling": {
                                "enabled": True,
                                "duration": "1m",
                                "max_attempts": 3,
                            }
                        },
                        "oauth2": {
                            "enabled": True,
                            "autocreate": True,
                            "introspection_url": (
                                "https://auth.meh.gripe/api/oidc/introspection"
                            ),
                            "introspection_timeout": "10s",
                            "client_id": "gamja",
                        },
                        "channels": {
                            "auto_join": [
                                "#kolamayermakers",
                                "#lf2607",
                            ],
                            "managed": [
                                {"name": "#kolamayermakers", "operators": ["pmuller"]},
                                {"name": "#lf2607", "operators": ["pmuller"]},
                            ],
                            "founder": "kolamayermakers",
                        },
                    }
                },
                {
                    "require": [
                        {"file": "ergo::configuration_directory"},
                        {"file": "ergo::data_directory"},
                        {"file": "ergo::tls_directory"},
                        {"file": "/usr/local/sbin/ergo-lldap-auth"},
                        {"file": "/usr/local/sbin/ergo-ensure-channel"},
                        {"file": "/etc/ergo/managed-channels.json"},
                        {"file": "/etc/ergo/ergo.motd"},
                        {"cmd": "ergo::bootstrap_tls_certificate"},
                        {"test": "ergo::configuration::required_pillar"},
                    ]
                },
            ]
        },
    }


def test_ergo_service_watches_managed_state_ids() -> None:
    """Test Ergo service low state."""
    assert _load_state("ergo/service.sls", _pillar()) == {
        "include": ["ergo.config"],
        "ergo::service::required_pillar": {
            "test.check_pillar": [
                {
                    "string": [
                        "ergo:service:user",
                        "ergo:service:group",
                        "ergo:service:home",
                        "ergo:service:unit_file",
                        "ergo:paths:configuration_file",
                        "ergo:paths:data_directory",
                        "ergo:paths:certificate_file",
                        "ergo:paths:certificate_key_file",
                        "ergo:paths:auth_script_file",
                        "ergo:paths:channel_script_file",
                        "ergo:paths:managed_channels_file",
                        "ergo:paths:motd_file",
                        "ergo:channels:founder",
                    ]
                },
                {"listing": ["ergo:channels:managed"]},
                {"failhard": True},
            ]
        },
        "ergo::managed_channels": {
            "cmd.run": [
                {
                    "name": (
                        "/usr/local/sbin/ergo-ensure-channel "
                        "--database /data/ergo/ircd.db --founder 'kolamayermakers' "
                        "--channels-file /etc/ergo/managed-channels.json"
                    )
                },
                {"runas": "ergo"},
                {
                    "unless": (
                        "/usr/local/sbin/ergo-ensure-channel --check "
                        "--database /data/ergo/ircd.db --founder 'kolamayermakers' "
                        "--channels-file /etc/ergo/managed-channels.json"
                    )
                },
                {
                    "require": [
                        {"file": "/usr/local/sbin/ergo-ensure-channel"},
                        {"file": "/etc/ergo/managed-channels.json"},
                        {"file": "ergo::data_directory"},
                        {"file": "/etc/ergo/ircd.yaml"},
                        {"service": "ergo::service"},
                        {"test": "ergo::service::required_pillar"},
                    ]
                },
            ]
        },
        "ergo::service_restart_after_managed_channels": {
            "cmd.run": [
                {"name": "systemctl restart ergo"},
                {"onchanges": [{"cmd": "ergo::managed_channels"}]},
                {"require": [{"cmd": "ergo::managed_channels"}]},
            ]
        },
        "ergo::unit_file": {
            "file.managed": [
                {"name": "/etc/systemd/system/ergo.service"},
                {"source": "salt://ergo/templates/ergo.service.j2"},
                {"template": "jinja"},
                {"user": "root"},
                {"group": "root"},
                {"mode": "0644"},
                {
                    "context": {
                        "service": {
                            "user": "ergo",
                            "group": "ergo",
                            "gid": 979,
                            "shell": "/usr/sbin/nologin",
                            "home": "/var/lib/ergo",
                            "system_user": True,
                            "create_home": False,
                            "unit_file": "/etc/systemd/system/ergo.service",
                        },
                        "paths": {
                            "configuration_directory": "/etc/ergo",
                            "configuration_file": "/etc/ergo/ircd.yaml",
                            "data_directory": "/data/ergo",
                            "tls_directory": "/etc/ergo/tls",
                            "certificate_file": "/etc/ergo/tls/fullchain.pem",
                            "certificate_key_file": "/etc/ergo/tls/privkey.pem",
                            "auth_script_file": "/usr/local/sbin/ergo-lldap-auth",
                            "channel_script_file": "/usr/local/sbin/ergo-ensure-channel",
                            "managed_channels_file": "/etc/ergo/managed-channels.json",
                            "motd_file": "/etc/ergo/ergo.motd",
                        },
                    }
                },
                {"require": [{"test": "ergo::service::required_pillar"}]},
            ]
        },
        "ergo::systemd_daemon_reload": {
            "module.run": [
                {"service.systemctl_reload": []},
                {"onchanges": [{"file": "ergo::unit_file"}]},
            ]
        },
        "ergo::service": {
            "service.running": [
                {"name": "ergo"},
                {"enable": True},
                {
                    "require": [
                        {"packages": "ergo"},
                        {"file": "/etc/ergo/ircd.yaml"},
                        {"file": "ergo::data_directory"},
                        {"file": "ergo::languages_directory_compatibility_symlink"},
                        {"file": "ergo::unit_file"},
                        {"module": "ergo::systemd_daemon_reload"},
                        {"test": "ergo::service::required_pillar"},
                    ]
                },
                {
                    "watch": [
                        {"packages": "ergo"},
                        {"file": "/etc/ergo/ircd.yaml"},
                        {"cmd": "ergo::bootstrap_tls_certificate"},
                        {"file": "/usr/local/sbin/ergo-lldap-auth"},
                        {"file": "/etc/ergo/ergo.motd"},
                        {"file": "ergo::unit_file"},
                    ]
                },
            ]
        },
    }


def test_ergo_configuration_template_renders_valid_private_irc_service() -> None:
    """Test rendered Ergo configuration."""
    pillar = _pillar()
    assert _is_string_object_dictionary(pillar["ergo"])
    assert _load_yaml_template("ergo/templates/ircd.yaml.j2", pillar["ergo"]) == {
        "network": {"name": "KolamAyerMakers"},
        "server": {
            "name": "irc.meh.gripe",
            "listeners": {
                ":6697": {
                    "tls": {
                        "cert": "/etc/ergo/tls/fullchain.pem",
                        "key": "/etc/ergo/tls/privkey.pem",
                    },
                    "proxy": False,
                    "min-tls-version": 1.2,
                },
                "127.0.0.1:8097": {"websocket": True},
            },
            "websockets": {"allowed-origins": ["https://irc.meh.gripe"]},
            "motd": "/etc/ergo/ergo.motd",
            "enforce-utf8": True,
            "lookup-hostnames": True,
            "forward-confirm-hostnames": True,
            "proxy-allowed-from": ["localhost"],
            "ip-cloaking": {
                "enabled": False,
                "enabled-for-always-on": True,
                "netname": "kolamayermakers",
                "cidr-len-ipv4": 32,
                "cidr-len-ipv6": 64,
                "num-bits": 64,
            },
            "check-ident": False,
            "coerce-ident": "~u",
            "max-sendq": "96KB",
        },
        "accounts": {
            "authentication-enabled": True,
            "registration": {"enabled": False, "allow-before-connect": False},
            "skip-server-password": True,
            "login-via-pass-command": False,
            "login-throttling": {
                "enabled": True,
                "duration": "1m",
                "max-attempts": 3,
            },
            "require-sasl": {"enabled": True, "exempted": []},
            "nick-reservation": {
                "enabled": True,
                "additional-nick-limit": 0,
                "method": "strict",
                "allow-custom-enforcement": False,
                "guest-nickname-format": "Guest-*",
                "force-guest-format": False,
                "force-nick-equals-account": True,
                "forbid-anonymous-nick-changes": True,
            },
            "multiclient": {
                "enabled": True,
                "allowed-by-default": True,
                "always-on": "opt-in",
                "auto-away": "opt-in",
            },
            "auth-script": {
                "enabled": True,
                "command": "/usr/local/sbin/ergo-lldap-auth",
                "args": [
                    "--ldap-uri",
                    "ldap://127.0.0.1:3890",
                    "--base-dn",
                    "dc=kolamayermakers,dc=org",
                    "--allowed-group",
                    "humans",
                    "--allowed-group",
                    "irc-bots",
                ],
                "autocreate": True,
                "timeout": "9s",
                "kill-timeout": "1s",
                "max-concurrency": 64,
            },
            "oauth2": {
                "enabled": True,
                "autocreate": True,
                "auth-script": False,
                "introspection-url": "https://auth.meh.gripe/api/oidc/introspection",
                "introspection-timeout": "10s",
                "client-id": "gamja",
                "client-secret": "",
            },
        },
        "channels": {
            "default-modes": "+ntC",
            "operator-only-creation": True,
            "registration": {"enabled": False, "operator-only": True},
            "auto-join": ["#kolamayermakers", "#lf2607"],
        },
        "logging": [
            {
                "method": "stderr",
                "type": "* -userinput -useroutput",
                "level": "info",
            }
        ],
        "datastore": {"path": "/data/ergo/ircd.db", "autoupgrade": True},
        "languages": {
            "enabled": True,
            "default": "en",
            "path": "/opt/packages/ergo/languages",
        },
        "limits": {
            "nicklen": 32,
            "identlen": 20,
            "realnamelen": 150,
            "channellen": 64,
            "awaylen": 390,
            "kicklen": 390,
            "topiclen": 390,
            "monitor-entries": 100,
            "whowas-entries": 100,
            "chan-list-modes": 100,
            "registration-messages": 1024,
            "multiline": {"max-bytes": 4096, "max-lines": 100},
            "fakelag": {
                "enabled": True,
                "window": "1s",
                "burst-limit": 5,
                "messages-per-window": 2,
                "cooldown": "2s",
                "command-budgets": {
                    "CHATHISTORY": 16,
                    "MARKREAD": 16,
                    "MONITOR": 1,
                    "WHO": 4,
                    "WEBPUSH": 1,
                },
            },
        },
        "history": {
            "enabled": True,
            "channel-length": 2048,
            "client-length": 256,
            "autoresize-window": "3d",
            "autoreplay-on-join": 0,
            "chathistory-maxmessages": 1000,
            "znc-maxmessages": 2048,
            "restrictions": {
                "expire-time": "1w",
                "query-cutoff": "none",
                "grace-period": "1h",
            },
            "persistent": {"enabled": False},
        },
    }


def test_ergo_configuration_template_accepts_multiple_websocket_origins() -> None:
    """Test Ergo can accept browser websocket origins from service aliases."""
    pillar = _pillar()
    assert _is_string_object_dictionary(pillar["ergo"])
    server = pillar["ergo"]["server"]
    assert _is_string_object_dictionary(server)
    server["websocket_origins"] = [
        "https://irc.dev.kolamayermakers.org",
        "https://irc.kolamayermakers.org",
    ]
    rendered_server = _load_yaml_template(
        "ergo/templates/ircd.yaml.j2", pillar["ergo"]
    )["server"]
    assert _is_string_object_dictionary(rendered_server)

    assert rendered_server["websockets"] == {
        "allowed-origins": [
            "https://irc.dev.kolamayermakers.org",
            "https://irc.kolamayermakers.org",
        ]
    }
