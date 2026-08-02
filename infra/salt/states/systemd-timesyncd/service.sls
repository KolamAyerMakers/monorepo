include:
  - systemd-timesyncd.config
  - systemd-timesyncd.firewall

{% set service = salt['pillar.get']('systemd-timesyncd:service', {}) %}

systemd-timesyncd::service::required_pillar:
  test.check_pillar:
    - string:
      - systemd-timesyncd:service:name
    - failhard: true

systemd-timesyncd::service:
  service.running:
    - name: {{ service.name }}
    - enable: true
    - require:
      - pkg: systemd-timesyncd::package
      - file: /etc/systemd/timesyncd.conf
      - file: /etc/nftables.d/45-systemd-timesyncd.nft
      - test: systemd-timesyncd::service::required_pillar
    - watch:
      - file: /etc/systemd/timesyncd.conf
