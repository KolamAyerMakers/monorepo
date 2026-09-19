kam_classroom:
  network_diagnostics:
    packages:
      - curl
      - ca-certificates
      - bind9-host
      - iputils-ping
      - inetutils-traceroute
      - iproute2
      - netcat-openbsd
      - procps
    traceroute:
      firewall_file: /etc/nftables.d/50-kam-classroom-traceroute.nft
      udp_port_range: 33434-33534
