packages:
  forgejo:
    version: 15.0.2
    arch:
      x86_64:
        libc: static
        url: https://codeberg.org/forgejo/forgejo/releases/download/v{version}/forgejo-{version}-linux-amd64
        checksum: sha256=d0e6f83ec24bc84eba90fdab48ad08b16f61e6b1e5095bf8483be849d860fdc8
      aarch64:
        libc: static
        url: https://codeberg.org/forgejo/forgejo/releases/download/v{version}/forgejo-{version}-linux-arm64
        checksum: sha256=ba8184bf8bd7aa25357fe4315000a4cea33d28e29ecb852823e9dbfeb38562f7
    scope: system
    raw_binary: true
    binaries:
      - forgejo
