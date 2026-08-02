packages:
  lsd:
    version: 1.2.0
    arch:
      x86_64:
        url: https://github.com/lsd-rs/lsd/releases/download/v{version}/lsd-v{version}-x86_64-unknown-linux-gnu.tar.gz
        checksum: sha256=57d3b5859254adcfb8374ce98159cca97a14959997d2ae1176d2cff59556d829
      aarch64:
        url: https://github.com/lsd-rs/lsd/releases/download/v{version}/lsd-v{version}-aarch64-unknown-linux-gnu.tar.gz
        checksum: sha256=48c069cf73a8ed0851f366afeac86e3a9b7db416133f45d033d31d123f819f26
    scope: system
    replaces_pkg: lsd
    binaries:
      - lsd
    strip_components: 1
