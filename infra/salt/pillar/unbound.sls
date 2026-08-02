unbound:
  listen_address: "127.0.0.1"
  port: 53
  auto_trust_anchor_file: "/var/lib/unbound/root.key"
  root_hints: null
  manage_resolv_conf: false
  service:
    user: unbound
    supplementary_groups: []
  firewall:
    enabled: true
