packages:
  d2:
    version: 0.7.1
    arch:
      x86_64:
        url: https://github.com/terrastruct/d2/releases/download/v{version}/d2-v{version}-linux-amd64.tar.gz
        checksum: sha256=eb172adf59f38d1e5a70ab177591356754ffaf9bebb84e0ca8b767dfb421dad7
      aarch64:
        url: https://github.com/terrastruct/d2/releases/download/v{version}/d2-v{version}-linux-arm64.tar.gz
        checksum: sha256=ce3a0b985a8f91335a826c254b3a88736fd81afcdd08b58f6c749d2add6864b0
    scope: system
    binaries:
      - d2
    strip_components: 1
