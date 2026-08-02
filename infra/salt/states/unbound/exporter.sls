include:
  - github.download_egress

{%- set version = salt['pillar.get']('unbound_exporter:version') %}
{%- set checksum = salt['pillar.get']('unbound_exporter:checksum') %}

unbound_exporter::download:
  file.managed:
    - name: /var/cache/salt/unbound_exporter-v{{ version }}.x86_64.deb
    - source: https://github.com/letsencrypt/unbound_exporter/releases/download/v{{ version }}/unbound_exporter-v{{ version }}.x86_64.deb
    - source_hash: {{ checksum }}
    - makedirs: true
    - require:
      - test: github::download_egress::ready
      - test: bootstrap::package_sources_ready

unbound_exporter::package:
  pkg.installed:
    - sources:
      - unbound_exporter: /var/cache/salt/unbound_exporter-v{{ version }}.x86_64.deb
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
