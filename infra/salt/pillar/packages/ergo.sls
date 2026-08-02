packages:
  ergo:
    version: 2.18.0
    arch:
      x86_64:
        url: https://github.com/ergochat/ergo/releases/download/v{version}/ergo-{version}-linux-x86_64.tar.gz
        checksum: sha256=cbd888d9f89224eced6af76dae4b729eaa41ea04afd2e85fe9be8169a790a1da
      aarch64:
        url: https://github.com/ergochat/ergo/releases/download/v{version}/ergo-{version}-linux-arm64.tar.gz
        checksum: sha256=d84188afae05bcbc3d01c18e4d62f0a5a395065b518d86c430ce75cc625fac63
    scope: system
    strip_components: 1
    binaries:
      - ergo
