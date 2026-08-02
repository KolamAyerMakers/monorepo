packages:
  golangci-lint:
    version: 2.11.4
    arch:
      x86_64:
        url: https://github.com/golangci/golangci-lint/releases/download/v{version}/golangci-lint-{version}-linux-amd64.tar.gz
        checksum: sha256=200c5b7503f67b59a6743ccf32133026c174e272b930ee79aa2aa6f37aca7ef1
      aarch64:
        url: https://github.com/golangci/golangci-lint/releases/download/v{version}/golangci-lint-{version}-linux-arm64.tar.gz
        checksum: sha256=3bcfa2e6f3d32b2bf5cd75eaa876447507025e0303698633f722a05331988db4
    scope: system
    binaries:
      - golangci-lint
    strip_components: 1
