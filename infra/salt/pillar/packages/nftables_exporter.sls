packages:
  nftables_exporter:
    version: 0.4.4
    arch:
      x86_64:
        libc: static
        url: https://github.com/metal-stack/nftables-exporter/releases/download/v{version}/nftables-exporter-linux-amd64
        checksum: sha256=3d26b237f9c4328037ced1b91695a003afd8075982730cf5e2df573b70eb3e1a
      aarch64:
        libc: static
        url: https://github.com/metal-stack/nftables-exporter/releases/download/v{version}/nftables-exporter-linux-arm64
        checksum: sha256=d8614ead50a41645de5fbb9491a3b1314e159806d1b05391d21ef6cff272e183
    scope: system
    binaries:
      - nftables_exporter
