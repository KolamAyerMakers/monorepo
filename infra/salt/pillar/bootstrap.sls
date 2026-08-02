bootstrap:
  package_egress:
    enabled: true
    users:
      - root
      - _apt
    # Temporary bootstrap resolvers used only until local Unbound is running.
    # This repairs first-run and half-run states where systemd-resolved is gone.
    nameservers:
      - 1.1.1.1
      - 9.9.9.9
    dns_ports:
      - 53
    http_ports:
      - 80
      - 443
