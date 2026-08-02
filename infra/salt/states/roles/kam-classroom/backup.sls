include:
  - roles.kam-classroom.packages
  - roles.kam-classroom.bot
  - ergo.service
  - lldap.service
  - authelia.service
  - forgejo.service

{% set backup = salt['pillar.get']('kam_classroom:backup', {}) %}

roles::kam_classroom::backup::required_pillar:
  test.check_pillar:
    - string:
      - kam_classroom:backup:root
      - kam_classroom:backup:maker_guide_database
      - kam_classroom:backup:maker_guide_config
      - kam_classroom:backup:ergo_data
      - kam_classroom:backup:lldap_data
      - kam_classroom:backup:authelia_data
      - kam_classroom:backup:forgejo_data
      - kam_classroom:backup:homes_data
    - integer:
      - kam_classroom:backup:retention_days
    - failhard: true

{{ backup.root }}:
  file.directory:
    - user: root
    - group: root
    - mode: '0700'
    - makedirs: true
    - require:
      - test: roles::kam_classroom::backup::required_pillar

/usr/local/sbin/classroom-backup:
  file.managed:
    - source: salt://roles/kam-classroom/files/classroom-backup
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - pkg: roles::kam_classroom::sqlite3

/etc/classroom-backup.conf:
  file.managed:
    - source: salt://roles/kam-classroom/templates/classroom-backup.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0600'
    - context:
        backup: {{ backup | yaml }}
    - require:
      - file: {{ backup.root }}
      - test: roles::kam_classroom::backup::required_pillar

/etc/systemd/system/classroom-backup.service:
  file.managed:
    - source: salt://roles/kam-classroom/files/classroom-backup.service
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /usr/local/sbin/classroom-backup
      - file: /etc/classroom-backup.conf

/etc/systemd/system/classroom-backup.timer:
  file.managed:
    - source: salt://roles/kam-classroom/files/classroom-backup.timer
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/systemd/system/classroom-backup.service

roles::kam_classroom::backup::systemd_reload:
  module.run:
    - service.systemctl_reload: []
    - onchanges:
      - file: /etc/systemd/system/classroom-backup.service
      - file: /etc/systemd/system/classroom-backup.timer

classroom-backup.timer:
  service.running:
    - enable: true
    - require:
      - file: /etc/systemd/system/classroom-backup.service
      - file: /etc/systemd/system/classroom-backup.timer
      - module: roles::kam_classroom::backup::systemd_reload
