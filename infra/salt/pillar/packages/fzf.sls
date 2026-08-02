packages:
  fzf:
    version: 0.71.0
    arch:
      x86_64:
        url: https://github.com/junegunn/fzf/releases/download/v{version}/fzf-{version}-linux_amd64.tar.gz
        checksum: sha256=22639bb38489dbca8acef57850cbb50231ab714d0e8e855ac52fae8b41233df4
      aarch64:
        url: https://github.com/junegunn/fzf/releases/download/v{version}/fzf-{version}-linux_arm64.tar.gz
        checksum: sha256=98b7d322efae9c37e4bfbbab1cbcd8722eb742d9399511f96375feb40cc35d1d
    scope: system
    replaces_pkg: fzf
    binaries:
      - fzf
