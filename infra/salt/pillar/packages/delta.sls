packages:
  delta:
    version: 0.19.1
    arch:
      x86_64:
        url: https://github.com/dandavison/delta/releases/download/{version}/delta-{version}-x86_64-unknown-linux-gnu.tar.gz
        checksum: sha256=b21fd5c32da694085f1bc1ab2daa81c01c48efaf5ce3137ba23102b824304c71
      aarch64:
        url: https://github.com/dandavison/delta/releases/download/{version}/delta-{version}-aarch64-unknown-linux-gnu.tar.gz
        checksum: sha256=0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5
    scope: system
    binaries:
      - delta
    strip_components: 1
