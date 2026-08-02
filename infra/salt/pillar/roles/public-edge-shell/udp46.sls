udp46:
  listen_ports:
    wireguard: 51820
    https-fallback: 443
    dns-fallback: 53
  upstream:
    host: void.hexod.net
    port: 51820
