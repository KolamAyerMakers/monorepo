rsyslog::cleanup::service:
  service.dead:
    - name: rsyslog
    - enable: false
    - onlyif:
      - fun: service.available
        args:
          - rsyslog

rsyslog::cleanup::package:
  pkg.purged:
    - name: rsyslog
    - require:
      - service: rsyslog::cleanup::service
