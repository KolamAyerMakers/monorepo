packages:
  chrony_exporter:
    version: 0.13.3
    arch:
      x86_64:
        libc: static
        url: https://github.com/SuperQ/chrony_exporter/releases/download/v{version}/chrony_exporter-{version}.linux-amd64.tar.gz
        checksum: sha256=cbb0d93b718bd62f4b13726771df94ed80c3f8a67a5813d3fbaefbcae514b33b
      aarch64:
        libc: static
        url: https://github.com/SuperQ/chrony_exporter/releases/download/v{version}/chrony_exporter-{version}.linux-arm64.tar.gz
        checksum: sha256=82941ba87e6477415ba5df336d4f88d943fe78f1a12c8d4af3eac157d543a741
    scope: system
    binaries:
      - chrony_exporter
    strip_components: 1
