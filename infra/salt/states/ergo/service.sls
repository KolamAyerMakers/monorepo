include:
  - ergo.config

{% set ergo = salt['pillar.get']('ergo', {}) %}
{% set service = ergo.get('service', {}) %}
{% set paths = ergo.get('paths', {}) %}
{% set channels = ergo.get('channels', {}) %}
{% set managed_channels = channels.get('managed', []) %}
{% set channel_script = paths.channel_script_file %}
{% set channel_database = paths.data_directory ~ '/ircd.db' %}
{% set channel_founder = channels.founder %}
{% set managed_channels_file = paths.managed_channels_file %}

ergo::service::required_pillar:
  test.check_pillar:
    - string:
      - ergo:service:user
      - ergo:service:group
      - ergo:service:home
      - ergo:service:unit_file
      - ergo:paths:configuration_file
      - ergo:paths:data_directory
      - ergo:paths:certificate_file
      - ergo:paths:certificate_key_file
      - ergo:paths:auth_script_file
      - ergo:paths:channel_script_file
      - ergo:paths:managed_channels_file
      - ergo:paths:motd_file
      - ergo:channels:founder
    - listing:
      - ergo:channels:managed
    - failhard: true

{% if managed_channels %}
ergo::managed_channels:
  cmd.run:
    - name: >-
        {{ channel_script }} --database {{ channel_database }} --founder '{{ channel_founder }}' --channels-file {{ managed_channels_file }}
    - runas: {{ service.user }}
    - unless: >-
        {{ channel_script }} --check --database {{ channel_database }} --founder '{{ channel_founder }}' --channels-file {{ managed_channels_file }}
    - require:
      - file: {{ paths.channel_script_file }}
      - file: {{ managed_channels_file }}
      - file: ergo::data_directory
      - file: {{ paths.configuration_file }}
      - service: ergo::service
      - test: ergo::service::required_pillar

ergo::service_restart_after_managed_channels:
  cmd.run:
    - name: systemctl restart ergo
    - onchanges:
      - cmd: ergo::managed_channels
    - require:
      - cmd: ergo::managed_channels

{% endif %}

ergo::unit_file:
  file.managed:
    - name: {{ service.unit_file }}
    - source: salt://ergo/templates/ergo.service.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        service: {{ service | yaml }}
        paths: {{ paths | yaml }}
    - require:
      - test: ergo::service::required_pillar

ergo::systemd_daemon_reload:
  module.run:
    - service.systemctl_reload: []
    - onchanges:
      - file: ergo::unit_file

ergo::service:
  service.running:
    - name: ergo
    - enable: true
    - require:
      - packages: ergo
      - file: {{ paths.configuration_file }}
      - file: ergo::data_directory
      - file: ergo::languages_directory_compatibility_symlink
      - file: ergo::unit_file
      - module: ergo::systemd_daemon_reload
      - test: ergo::service::required_pillar
    - watch:
      - packages: ergo
      - file: {{ paths.configuration_file }}
      - cmd: ergo::bootstrap_tls_certificate
      - file: {{ paths.auth_script_file }}
      - file: {{ paths.motd_file }}
      - file: ergo::unit_file
