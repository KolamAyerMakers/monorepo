include:
  - node_exporter.package

# Clean up the legacy manually-installed unit (node-exporter.service with a
# dash) so the Salt-managed node_exporter.service can own port 9100.
node_exporter::legacy_service::dead:
  service.dead:
    - name: node-exporter
    - enable: false
    - onlyif:
      - fun: file.file_exists
        path: /etc/systemd/system/node-exporter.service

/etc/systemd/system/node-exporter.service:
  file.absent:
    - require:
      - service: node_exporter::legacy_service::dead

node_exporter::legacy_service::daemon_reload:
  module.run:
    - service.systemctl_reload: []
    - onchanges:
      - file: /etc/systemd/system/node-exporter.service

node_exporter::group:
  group.present:
    - name: node_exporter
    - system: true

node_exporter::user:
  user.present:
    - name: node_exporter
    - system: true
    - shell: /usr/sbin/nologin
    - home: /nonexistent
    - createhome: false
    - gid: node_exporter
    - require:
      - group: node_exporter::group

/etc/systemd/system/node_exporter.service:
  file.managed:
    - source: salt://node_exporter/files/node_exporter.service
    - user: root
    - group: root
    - mode: '0644'

node_exporter::service:
  service.running:
    - name: node_exporter
    - enable: true
    - require:
      - packages: node_exporter
      - user: node_exporter::user
      - file: /etc/systemd/system/node_exporter.service
      - file: /etc/systemd/system/node-exporter.service
      - module: node_exporter::legacy_service::daemon_reload
    - watch:
      - packages: node_exporter
      - file: /etc/systemd/system/node_exporter.service
