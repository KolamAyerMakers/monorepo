{%- from "bootstrap/macros/packages.sls" import bootstrap_package_installed -%}

include:
  - bootstrap.packages

{% set quotas = salt['pillar.get']('quotas', {}) -%}
{% set filesystems = quotas.get('filesystems', {}) -%}
{% set quota_configuration = {'filesystems': filesystems} -%}

quotas::required_pillar:
  test.check_pillar:
    - dictionary:
      - quotas:filesystems
{% for filesystem_name, filesystem in filesystems.items() %}
      - quotas:filesystems:{{ filesystem_name }}
      - quotas:filesystems:{{ filesystem_name }}:group_defaults
      - quotas:filesystems:{{ filesystem_name }}:user_overrides
    - string:
      - quotas:filesystems:{{ filesystem_name }}:path
{%   for group_name in filesystem.get('group_defaults', {}) %}
    - integer:
      - quotas:filesystems:{{ filesystem_name }}:group_defaults:{{ group_name }}:soft_block_limit_kib
      - quotas:filesystems:{{ filesystem_name }}:group_defaults:{{ group_name }}:hard_block_limit_kib
{%   endfor %}
{%   for username in filesystem.get('user_overrides', {}) %}
    - integer:
      - quotas:filesystems:{{ filesystem_name }}:user_overrides:{{ username }}:soft_block_limit_kib
      - quotas:filesystems:{{ filesystem_name }}:user_overrides:{{ username }}:hard_block_limit_kib
{%   endfor %}
{% endfor %}
    - failhard: true

{{ bootstrap_package_installed('quota', state_identifier='quotas::package') }}

/usr/local/sbin/apply-user-quotas:
  file.managed:
    - source: salt://quotas/files/apply_user_quotas.py
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - pkg: quotas::package
      - test: quotas::required_pillar

/etc/quotas:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'

/etc/quotas/user-quotas.json:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: '{{ quota_configuration | tojson }}'
    - require:
      - file: /etc/quotas
      - test: quotas::required_pillar

/etc/systemd/system/apply-user-quotas.service:
  file.managed:
    - source: salt://quotas/templates/apply-user-quotas.service.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /usr/local/sbin/apply-user-quotas
      - file: /etc/quotas/user-quotas.json
      - test: quotas::required_pillar

quotas::systemd_daemon_reload:
  module.run:
    - service.systemctl_reload: []
    - onchanges:
      - file: /etc/systemd/system/apply-user-quotas.service

quotas::service:
  service.running:
    - name: apply-user-quotas
    - enable: true
    - require:
      - pkg: quotas::package
      - file: /usr/local/sbin/apply-user-quotas
      - file: /etc/quotas/user-quotas.json
      - file: /etc/systemd/system/apply-user-quotas.service
      - module: quotas::systemd_daemon_reload
      - test: quotas::required_pillar
    - watch:
      - file: /usr/local/sbin/apply-user-quotas
      - file: /etc/quotas/user-quotas.json
      - file: /etc/systemd/system/apply-user-quotas.service
