packages:
  glow:
    version: 2.1.2
    arch:
      x86_64:
        libc: static
        url: https://github.com/charmbracelet/glow/releases/download/v{version}/glow_{version}_Linux_x86_64.tar.gz
        checksum: sha256=6063d4f2af8a82a5f4bba0831e165de9381660aa8b41df4816d0106a265b07d5
      aarch64:
        libc: static
        url: https://github.com/charmbracelet/glow/releases/download/v{version}/glow_{version}_Linux_arm64.tar.gz
        checksum: sha256=cf63abebcb50b72909db965d78290e7cecbf17a900e84705dc84addbb6952099
    scope: system
    binaries:
      - glow
    strip_components: 1
    completions:
      999-completion-glow.sh: completions/glow.bash
