include:
  - lldap.config

{% set lldap = salt['pillar.get']('lldap', {}) %}
{% set service = lldap.get('service', {}) %}
{% set paths = lldap.get('paths', {}) %}

lldap::service::required_pillar:
  test.check_pillar:
    - string:
      - lldap:service:user
      - lldap:service:group
      - lldap:service:home
      - lldap:service:unit_file
      - lldap:paths:configuration_file
      - lldap:paths:data_directory
      - lldap:paths:secret_environment_file
    - failhard: true

lldap::unit_file:
  file.managed:
    - name: {{ service.unit_file }}
    - source: salt://lldap/templates/lldap.service.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        service: {{ service | yaml }}
        paths: {{ paths | yaml }}
    - require:
      - test: lldap::service::required_pillar

lldap::systemd_daemon_reload:
  module.run:
    - service.systemctl_reload: []
    - onchanges:
      - file: lldap::unit_file

lldap::service:
  service.running:
    - name: lldap
    - enable: true
    - require:
      - packages: lldap
      - file: {{ paths.configuration_file }}
      - file: lldap::data_directory
      - file: lldap::secret_environment_file
      - file: lldap::unit_file
      - module: lldap::systemd_daemon_reload
      - test: lldap::service::required_pillar
    - watch:
      - packages: lldap
      - file: {{ paths.configuration_file }}
      - file: lldap::unit_file
