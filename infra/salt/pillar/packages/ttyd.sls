packages:
  ttyd:
    version: 1.7.7
    arch:
      x86_64:
        url: https://github.com/tsl0922/ttyd/releases/download/{version}/ttyd.x86_64
        checksum: sha256=8a217c968aba172e0dbf3f34447218dc015bc4d5e59bf51db2f2cd12b7be4f55
      aarch64:
        url: https://github.com/tsl0922/ttyd/releases/download/{version}/ttyd.aarch64
        checksum: sha256=b38acadd89d1d396a0f5649aa52c539edbad07f4bc7348b27b4f4b7219dd4165
    scope: system
    binaries:
      - ttyd
