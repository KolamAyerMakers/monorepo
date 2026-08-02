packages:
  starship:
    version: 1.24.2
    arch:
      x86_64:
        url: https://github.com/starship/starship/releases/download/v{version}/starship-x86_64-unknown-linux-gnu.tar.gz
        checksum: sha256=3f12f61883ff324c1dbe7b885fa125d5490960e5cad6a12eeaa34695ec1b5744
      aarch64:
        url: https://github.com/starship/starship/releases/download/v{version}/starship-aarch64-unknown-linux-musl.tar.gz
        checksum: sha256=56b9ff412bbf374d29b99e5ac09a849124cb37a0a13121e8470df32de53c1ea6
    scope: system
    binaries:
      - starship
