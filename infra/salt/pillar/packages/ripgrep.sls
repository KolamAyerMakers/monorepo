packages:
  ripgrep:
    version: 15.1.0
    arch:
      x86_64:
        url: https://github.com/BurntSushi/ripgrep/releases/download/{version}/ripgrep-{version}-x86_64-unknown-linux-musl.tar.gz
        checksum: sha256=1c9297be4a084eea7ecaedf93eb03d058d6faae29bbc57ecdaf5063921491599
      aarch64:
        url: https://github.com/BurntSushi/ripgrep/releases/download/{version}/ripgrep-{version}-aarch64-unknown-linux-gnu.tar.gz
        checksum: sha256=393fede2914f258976ec33a72b8b16cd3ec3d104565ab0b436ab818e73b20231
    scope: system
    binaries:
      - rg
    strip_components: 1
    manpages:
      rg.1: doc/rg.1
    completions:
      999-completion-ripgrep.sh: complete/rg.bash
