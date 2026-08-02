packages:
  rtk:
    version: 0.34.3
    arch:
      x86_64:
        url: https://github.com/rtk-ai/rtk/releases/download/v{version}/rtk-x86_64-unknown-linux-musl.tar.gz
        checksum: sha256=a607c17bfdccc1d48dc94ca81cd3a545523329df6a378368fd175d8023425ea5
      aarch64:
        url: https://github.com/rtk-ai/rtk/releases/download/v{version}/rtk-aarch64-unknown-linux-musl.tar.gz
        checksum: sha256=0a3afae8435a352c32eaacb8ecd76953146928191fefc8b2de703f3adf10c9f8
    scope: system
    binaries:
      - rtk
