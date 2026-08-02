packages:
  mcfly:
    version: 0.9.4
    arch:
      x86_64:
        url: https://github.com/cantino/mcfly/releases/download/v{version}/mcfly-v{version}-x86_64-unknown-linux-musl.tar.gz
        checksum: sha256=72d2c6fdaa111ac96c2cf725fc40e313e2856643482be58608911a09440313f1
      aarch64:
        url: https://github.com/cantino/mcfly/releases/download/v{version}/mcfly-v{version}-aarch64-unknown-linux-musl.tar.gz
        checksum: sha256=57eb23c3c40b3a7675dc1fe3b785501a6a41598b9b3cbe35d80f8d65267cf1cd
    scope: system
    binaries:
      - mcfly
