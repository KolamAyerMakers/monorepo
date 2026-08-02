packages:
  bat:
    version: 0.26.1
    arch:
      x86_64:
        url: https://github.com/sharkdp/bat/releases/download/v{version}/bat-v{version}-x86_64-unknown-linux-gnu.tar.gz
        checksum: sha256=726f04c8f576a7fd18b7634f1bbf2f915c43494c1c0f013baa3287edb0d5a2a3
      aarch64:
        url: https://github.com/sharkdp/bat/releases/download/v{version}/bat-v{version}-aarch64-unknown-linux-gnu.tar.gz
        checksum: sha256=422eb73e11c854fddd99f5ca8461c2f1d6e6dce0a2a8c3d5daade5ffcb6564aa
    scope: system
    replaces_pkg: bat
    binaries:
      - bat
    strip_components: 1
    completions:
      999-completion-bat.sh: autocomplete/bat.bash
