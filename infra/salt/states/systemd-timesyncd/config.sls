{% set configuration = salt['pillar.get']('systemd-timesyncd:config', {}) %}
systemd-timesyncd::config::required_pillar:
  test.check_pillar:
    - listing:
      - systemd-timesyncd:config:ntp
      - systemd-timesyncd:config:fallback_ntp
    - failhard: true

/etc/systemd/timesyncd.conf:
  file.managed:
    - source: salt://systemd-timesyncd/timesyncd.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        configuration: {{ configuration | yaml }}
    - require:
      - pkg: systemd-timesyncd::package
      - test: systemd-timesyncd::config::required_pillar
