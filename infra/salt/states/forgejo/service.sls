include:
  - forgejo.config

{% set forgejo = salt['pillar.get']('forgejo', {}) %}
{% set service = forgejo.get('service', {}) %}
{% set paths = forgejo.get('paths', {}) %}

forgejo::service::required_pillar:
  test.check_pillar:
    - string:
      - forgejo:service:user
      - forgejo:service:group
      - forgejo:service:home
      - forgejo:service:unit_file
      - forgejo:paths:configuration_file
      - forgejo:paths:data_directory
      - forgejo:paths:log_directory
      - forgejo:paths:ssh_directory
    - failhard: true

forgejo::unit_file:
  file.managed:
    - name: {{ service.unit_file }}
    - source: salt://forgejo/templates/forgejo.service.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        service: {{ service | yaml }}
        paths: {{ paths | yaml }}
    - require:
      - test: forgejo::service::required_pillar

forgejo::systemd_daemon_reload:
  module.run:
    - service.systemctl_reload: []
    - onchanges:
      - file: forgejo::unit_file

forgejo::service:
  service.running:
    - name: forgejo
    - enable: true
    - require:
      - packages: forgejo
      - pkg: forgejo::git
      - pkg: forgejo::git_lfs
      - file: {{ paths.configuration_file }}
      - file: forgejo::data_directory
      - file: forgejo::log_directory
      - file: forgejo::ssh_directory
      - file: forgejo::unit_file
      - module: forgejo::systemd_daemon_reload
      - test: forgejo::service::required_pillar
    - watch:
      - packages: forgejo
      - file: {{ paths.configuration_file }}
      - file: forgejo::obsolete_custom_footer_template
      - file: forgejo::obsolete_head_navbar_template
      - file: forgejo::unit_file
