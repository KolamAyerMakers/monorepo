packages:
  uv:
    version: 0.11.3
    arch:
      x86_64:
        url: https://github.com/astral-sh/uv/releases/download/{version}/uv-x86_64-unknown-linux-gnu.tar.gz
        checksum: sha256=c0f3236f146e55472663cfbcc9be3042a9f1092275bbe3fe2a56a6cbfd3da5ce
      aarch64:
        url: https://github.com/astral-sh/uv/releases/download/{version}/uv-aarch64-unknown-linux-gnu.tar.gz
        checksum: sha256=placeholder
    scope: system
    binaries:
      - uv
      - uvx
    strip_components: 1
