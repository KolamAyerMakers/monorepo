packages:
  fx:
    version: 39.2.0
    arch:
      x86_64:
        url: https://github.com/antonmedv/fx/releases/download/{version}/fx_linux_amd64
        checksum: sha256=17ea6549c7cf0b8be5ec109d04da7fbf1d5de9f7b99d957a6215081933528afe
      aarch64:
        url: https://github.com/antonmedv/fx/releases/download/{version}/fx_linux_arm64
        checksum: sha256=85ea8435b0a80b6d31ffa9f61ac9b67d9bb8f0ffffabdfe5e7e587b07a0a0684
    scope: system
    binaries:
      - fx
