ergo:
  service:
    user: ergo
    group: ergo
    gid: 979
    shell: /usr/sbin/nologin
    home: /var/lib/ergo
    system_user: true
    create_home: false
    unit_file: /etc/systemd/system/ergo.service
  paths:
    configuration_directory: /etc/ergo
    configuration_file: /etc/ergo/ircd.yaml
    data_directory: /var/lib/ergo
    tls_directory: /etc/ergo/tls
    certificate_file: /etc/ergo/tls/fullchain.pem
    certificate_key_file: /etc/ergo/tls/privkey.pem
    auth_script_file: /usr/local/sbin/ergo-lldap-auth
    channel_script_file: /usr/local/sbin/ergo-ensure-channel
    managed_channels_file: /etc/ergo/managed-channels.json
    cert_sync_script: /usr/local/sbin/ergo-sync-caddy-cert
    cert_sync_service: /etc/systemd/system/ergo-sync-caddy-cert.service
    cert_sync_timer: /etc/systemd/system/ergo-sync-caddy-cert.timer
    motd_file: /etc/ergo/ergo.motd
  network:
    name: Ergo
  server:
    name: localhost
    websocket_origin: http://localhost
    lookup_hostnames: false
    forward_confirm_hostnames: true
    proxy_allowed_from:
      - localhost
    ip_cloaking:
      enabled: true
      enabled_for_always_on: true
      netname: irc
      cidr_len_ipv4: 32
      cidr_len_ipv6: 64
      num_bits: 64
  listeners:
    irc:
      address: :6697
    websocket:
      address: 127.0.0.1:8097
  auth:
    ldap_uri: ldap://127.0.0.1:3890
    base_dn: dc=example,dc=com
    required_group: ''
    allowed_groups: []
  accounts:
    login_throttling:
      enabled: true
      duration: 1m
      max_attempts: 3
  oauth2:
    enabled: false
    autocreate: true
    introspection_url: ''
    introspection_timeout: 10s
    client_id: ''
    client_secret: ''
  channels:
    auto_join: []
    managed: []
    founder: ergo
  motd:
    contents: |
      Ergo IRC
