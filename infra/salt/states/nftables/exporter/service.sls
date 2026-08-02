include:
  - nftables.exporter.package

nftables_exporter::group:
  group.present:
    - name: nftables_exporter
    - system: true

nftables_exporter::user:
  user.present:
    - name: nftables_exporter
    - system: true
    - shell: /usr/sbin/nologin
    - home: /nonexistent
    - createhome: false
    - gid: nftables_exporter
    - require:
      - group: nftables_exporter::group

/etc/nftables_exporter.yaml:
  file.managed:
    - source: salt://nftables/exporter/files/nftables_exporter.yaml
    - user: root
    - group: root
    - mode: '0644'

/etc/systemd/system/nftables_exporter.service:
  file.managed:
    - source: salt://nftables/exporter/files/nftables_exporter.service
    - user: root
    - group: root
    - mode: '0644'

nftables_exporter::service:
  service.running:
    - name: nftables_exporter
    - enable: true
    - require:
      - packages: nftables_exporter
      - user: nftables_exporter::user
      - file: /etc/systemd/system/nftables_exporter.service
      - file: /etc/nftables_exporter.yaml
    - watch:
      - packages: nftables_exporter
      - file: /etc/systemd/system/nftables_exporter.service
      - file: /etc/nftables_exporter.yaml
