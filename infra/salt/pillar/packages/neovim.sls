packages:
  neovim:
    version: 0.12.0
    arch:
      x86_64:
        url: https://github.com/neovim/neovim/releases/download/v{version}/nvim-linux-x86_64.tar.gz
        checksum: sha256=160b69125defb16e60b283b69be112fd4850d67ac8f9a752328c20ad43ec34af
      aarch64:
        url: https://github.com/neovim/neovim/releases/download/v{version}/nvim-linux-arm64.tar.gz
        checksum: sha256=89024e7be2ef3c8f08e9c002b1eb3e3b36672ee44bd6343cf2d168d38b3736b2
    scope: system
    binaries:
      - nvim
    strip_components: 1
    bin_subdir: bin
