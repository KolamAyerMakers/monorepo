nftables:
  default_policies:
    input: drop
    forward: drop
    output: drop
  icmp:
    ipv4_echo: true
    ipv6_echo: true
    ipv6_control: true
  ingress:
    tcp_ports: []
