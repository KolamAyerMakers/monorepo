{% from "roles/kam-classroom/domain_helpers.sls" import https_url, ldap_base_distinguished_name, public_hostname with context %}
{% set ergo_data_directory = '/data/ergo' %}

ergo:
  paths:
    data_directory: {{ ergo_data_directory }}
  network:
    name: KolamAyerMakers
  server:
    name: {{ public_hostname }}
    websocket_origins:
      - https://{{ public_hostname }}
    lookup_hostnames: true
    forward_confirm_hostnames: true
    proxy_allowed_from:
      - localhost
    ip_cloaking:
      enabled: false
      enabled_for_always_on: true
      netname: kolamayermakers
      cidr_len_ipv4: 32
      cidr_len_ipv6: 64
      num_bits: 64
  auth:
    ldap_uri: ldap://127.0.0.1:3890
    base_dn: {{ ldap_base_distinguished_name }}
    required_group: humans
    allowed_groups:
      - humans
      - irc-bots
  accounts:
    login_throttling:
      enabled: true
      duration: 1m
      max_attempts: 3
  oauth2:
    enabled: true
    autocreate: true
    introspection_url: {{ https_url('auth') }}api/oidc/introspection
    introspection_timeout: 10s
    client_id: gamja
  channels:
    auto_join: []
    managed:
      - name: "#kolamayermakers"
        operators:
          - pmuller
      - name: "#lf2607"
        operators:
          - pmuller
    founder: kolamayermakers
  motd:
    source: salt://roles/kam-classroom/files/ergo.motd

gamja:
  server:
    websocket_url: wss://{{ public_hostname }}/irc/webirc
    autojoin:
      - "#kolamayermakers"
      - "#lf2607"
  oauth2:
    url: {{ https_url('auth') | trim('/') }}
    client_id: gamja
    scope: openid profile groups
