packages:
  fd:
    version: 10.4.2
    arch:
      x86_64:
        url: https://github.com/sharkdp/fd/releases/download/v{version}/fd-v{version}-x86_64-unknown-linux-gnu.tar.gz
        checksum: sha256=def59805cd14b5651b68990855f426ad087f3b96881296d963910431ba3143c8
      aarch64:
        url: https://github.com/sharkdp/fd/releases/download/v{version}/fd-v{version}-aarch64-unknown-linux-gnu.tar.gz
        checksum: sha256=6c51f7c5446b3338b1e401ff15dc194c590bb2fa64fd43ff3278300f073adec5
    scope: system
    binaries:
      - fd
    strip_components: 1
    completions:
      999-completion-fd.sh: autocomplete/fd.bash
