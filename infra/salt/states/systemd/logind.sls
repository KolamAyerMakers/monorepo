{% set config = salt['pillar.get']('systemd:logind:config') %}

/etc/systemd/logind.conf:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - source: salt://systemd/templates/logind.conf.j2
    - context:
        config: {{ config | yaml }}
