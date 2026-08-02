dns-nftsets:
  configuration:
    path: /etc/dns-nftsets/configuration.jsonl
    resolver:
      address: 127.0.0.1
      port: 53
      timeout: 2.0
      lifetime: 5.0
    ttl:
      minimum_seconds: 60
      maximum_seconds: 86400
    set_timeout: 24h
  service:
    name: dns-nftsets
    script_path: /usr/local/libexec/dns-nftsets
    unit_file: /etc/systemd/system/dns-nftsets.service
    timer_file: /etc/systemd/system/dns-nftsets.timer
    on_boot: 10s
    on_unit_active: 30s
    accuracy: 5s
