packages:
  presenterm:
    version: 0.16.1
    arch:
      x86_64:
        libc: musl
        url: https://github.com/mfontanini/presenterm/releases/download/v{version}/presenterm-{version}-x86_64-unknown-linux-musl.tar.gz
        checksum: sha256=87512d7c88c3d961c7687aca3519f83c2b7611a550cf769c67c6f7948e8b8f54
      aarch64:
        libc: musl
        url: https://github.com/mfontanini/presenterm/releases/download/v{version}/presenterm-{version}-aarch64-unknown-linux-musl.tar.gz
        checksum: sha256=c03c3744609d61587aac9dda4f431912748bd70d88d4fa6c0440b079001c64c3
    scope: system
    binaries:
      - presenterm
    strip_components: 1
