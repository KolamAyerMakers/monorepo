packages:
  blocky:
    version: 0.29.0
    arch:
      x86_64:
        libc: static
        url: https://github.com/0xERR0R/blocky/releases/download/v{version}/blocky_v{version}_Linux_x86_64.tar.gz
        checksum: sha256=ce70e5ef992a8eb980cf05e2902a63f9ee27296e1c69114d6dd6506549388428
      aarch64:
        libc: static
        url: https://github.com/0xERR0R/blocky/releases/download/v{version}/blocky_v{version}_Linux_arm64.tar.gz
        checksum: sha256=89e127a19dcd226ab6ff807688f18b5f995b71906fd386561f1c46dfd9af3491
    scope: system
    binaries:
      - blocky
    strip_components: 0
