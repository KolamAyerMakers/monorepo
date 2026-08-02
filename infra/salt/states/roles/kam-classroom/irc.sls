include:
  - ergo.service
  - gamja
  - roles.kam-classroom.caddy
  - nftables

{% set ergo = salt['pillar.get']('ergo', {}) %}
{% set paths = ergo.get('paths', {}) %}
{% set server = ergo.get('server', {}) %}
{% set service = ergo.get('service', {}) %}
{% set listeners = ergo.get('listeners', {}) %}

roles::kam_classroom::irc::required_pillar:
  test.check_pillar:
    - string:
      - ergo:service:user
      - ergo:service:group
      - ergo:paths:cert_sync_script
      - ergo:paths:cert_sync_service
      - ergo:paths:cert_sync_timer
      - ergo:paths:tls_directory
      - ergo:paths:certificate_file
      - ergo:paths:certificate_key_file
      - ergo:server:name
      - ergo:listeners:irc:address
    - failhard: true

{{ paths.cert_sync_script }}:
  file.managed:
    - source: salt://roles/kam-classroom/templates/ergo-sync-caddy-cert.sh.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0755'
    - context:
        paths: {{ paths | yaml }}
        server: {{ server | yaml }}
        service: {{ service | yaml }}
    - require:
      - test: roles::kam_classroom::irc::required_pillar

roles::kam_classroom::ergo_caddy_certificate_sync:
  cmd.run:
    - name: {{ paths.cert_sync_script }} --wait-seconds 120 {{ server.name }}
    - unless: {{ paths.cert_sync_script }} --check {{ server.name }}
    - require:
      - file: {{ paths.cert_sync_script }}
      - service: kam-classroom::caddy::service
      - file: ergo::tls_directory
      - test: roles::kam_classroom::irc::required_pillar
    - require_in:
      - service: ergo::service
    - watch_in:
      - service: ergo::service

{{ paths.cert_sync_service }}:
  file.managed:
    - source: salt://roles/kam-classroom/templates/ergo-sync-caddy-cert.service.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        paths: {{ paths | yaml }}
        server: {{ server | yaml }}
    - require:
      - file: {{ paths.cert_sync_script }}
      - test: roles::kam_classroom::irc::required_pillar

{{ paths.cert_sync_timer }}:
  file.managed:
    - source: salt://roles/kam-classroom/templates/ergo-sync-caddy-cert.timer.j2
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - test: roles::kam_classroom::irc::required_pillar

roles::kam_classroom::ergo_cert_sync_systemd_daemon_reload:
  module.run:
    - service.systemctl_reload: []
    - onchanges:
      - file: {{ paths.cert_sync_service }}
      - file: {{ paths.cert_sync_timer }}

roles::kam_classroom::ergo_cert_sync_timer:
  service.running:
    - name: ergo-sync-caddy-cert.timer
    - enable: true
    - require:
      - file: {{ paths.cert_sync_service }}
      - file: {{ paths.cert_sync_timer }}
      - module: roles::kam_classroom::ergo_cert_sync_systemd_daemon_reload
      - test: roles::kam_classroom::irc::required_pillar

roles::kam_classroom::irc::firewall:
  nftables_file.managed:
    - name: /etc/nftables.d/50-kam-classroom-irc.nft
    - header: "# Kolam Ayer Makers classroom IRC TLS policy"
    - counters:
      - input_irc_tls
    - chains:
      - name: input
        position: '50'
    - rules:
      - chain: input
        position: '20'
        rule: >-
          tcp dport 6697 counter name "input_irc_tls"
          accept comment "kolam ayer makers classroom irc tls"
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/nftables.d
      - test: roles::kam_classroom::irc::required_pillar
    - watch_in:
      - cmd: nftables::validate
