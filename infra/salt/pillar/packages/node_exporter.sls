packages:
  node_exporter:
    version: 1.11.1
    arch:
      x86_64:
        libc: static
        url: https://github.com/prometheus/node_exporter/releases/download/v{version}/node_exporter-{version}.linux-amd64.tar.gz
        checksum: sha256=9f5ea48e5bc7b656f8a91a32e7d7deb89f70f73dabd0d974418aca15f37d6810
      aarch64:
        libc: static
        url: https://github.com/prometheus/node_exporter/releases/download/v{version}/node_exporter-{version}.linux-arm64.tar.gz
        checksum: sha256=ba1886efbd76cb96b0087c695ea8d1b9cb6e8aa946c996d744e9ee16c8e3591a
    scope: system
    binaries:
      - node_exporter
    strip_components: 1
