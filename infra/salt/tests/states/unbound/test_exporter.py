"""Tests for Unbound exporter states."""

from __future__ import annotations

import importlib
import textwrap
from typing import Protocol, cast

from tests.support.paths import SALTSTACK_DIRECTORY


class _Template(Protocol):
    def render(self, **context: object) -> str:
        """Render the template with test context."""
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


class _SaltNamespace:
    def __init__(self, pillar: dict[str, object]) -> None:
        self._pillar: dict[str, object] = pillar

    def __getitem__(self, key: str) -> object:
        if key == "pillar.get":
            return self.pillar_get
        raise KeyError(key)

    def pillar_get(self, key: str, default: object = None) -> object:
        """Return pillar data for the requested key."""
        current = self._pillar
        parts = key.split(":")
        for part in parts[:-1]:
            value = current.get(part)
            if not isinstance(value, dict):
                return default
            current = cast(dict[str, object], value)
        return current.get(parts[-1], default)


def _render_state(pillar: dict[str, object]) -> str:
    jinja2 = importlib.import_module("jinja2")
    environment_factory = cast(_EnvironmentFactory, getattr(jinja2, "Environment"))
    loader_factory = cast(_LoaderFactory, getattr(jinja2, "FileSystemLoader"))
    environment = environment_factory(
        loader=loader_factory(str(SALTSTACK_DIRECTORY / "states")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = environment.get_template("unbound/exporter.sls")
    return template.render(salt=_SaltNamespace(pillar))


def test_exporter_download_requires_shared_github_egress() -> None:
    """Test that Unbound exporter download requires populated GitHub sets."""
    rendered = _render_state(
        {
            "unbound_exporter": {
                "version": "0.4.6",
                "checksum": "sha256=abc123",
            },
        }
    )

    assert rendered == textwrap.dedent(
        """\
        include:
          - github.download_egress
        unbound_exporter::download:
          file.managed:
            - name: /var/cache/salt/unbound_exporter-v0.4.6.x86_64.deb
            - source: https://github.com/letsencrypt/unbound_exporter/releases/download/v0.4.6/unbound_exporter-v0.4.6.x86_64.deb
            - source_hash: sha256=abc123
            - makedirs: true
            - require:
              - test: github::download_egress::ready
              - test: bootstrap::package_sources_ready

        unbound_exporter::package:
          pkg.installed:
            - sources:
              - unbound_exporter: /var/cache/salt/unbound_exporter-v0.4.6.x86_64.deb
            - require:
              - file: unbound_exporter::download

        unbound_exporter::group:
          group.present:
            - name: unbound_exporter
            - system: true

        unbound_exporter::user:
          user.present:
            - name: unbound_exporter
            - system: true
            - shell: /usr/sbin/nologin
            - home: /nonexistent
            - createhome: false
            - gid: unbound_exporter
            - require:
              - group: unbound_exporter::group

        /etc/systemd/system/unbound_exporter.service:
          file.managed:
            - source: salt://unbound/files/unbound_exporter.service
            - user: root
            - group: root
            - mode: '0644'

        unbound_exporter::service:
          service.running:
            - name: unbound_exporter
            - enable: true
            - require:
              - pkg: unbound_exporter::package
              - user: unbound_exporter::user
              - file: /etc/systemd/system/unbound_exporter.service
              - service: unbound::service
            - watch:
              - pkg: unbound_exporter::package
              - file: /etc/systemd/system/unbound_exporter.service
        """
    ).removesuffix("\n")
