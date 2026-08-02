packages:
  just:
    version: 1.48.1
    arch:
      x86_64:
        url: https://github.com/casey/just/releases/download/{version}/just-{version}-x86_64-unknown-linux-musl.tar.gz
        checksum: sha256=9293e553ce401d1b524bf4e104918f72f268e3f9c6827e0055fe98d84a1b2522
      aarch64:
        url: https://github.com/casey/just/releases/download/{version}/just-{version}-aarch64-unknown-linux-musl.tar.gz
        checksum: sha256=3308721b991cf88cf2b9bbb3b31ac40550ec61a0c9b6fc011564e25e87964030
    scope: system
    binaries:
      - just
