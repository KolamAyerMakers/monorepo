packages:
  victorialogs:
    version: 1.50.0
    arch:
      x86_64:
        libc: static
        url: https://github.com/VictoriaMetrics/VictoriaLogs/releases/download/v{version}/victoria-logs-linux-amd64-v{version}.tar.gz
        checksum: sha256=ab8a4503d88efe62ee72c51da2cf0215890e84ac4f6e1c6ab07d1318972f5ddc
      aarch64:
        libc: static
        url: https://github.com/VictoriaMetrics/VictoriaLogs/releases/download/v{version}/victoria-logs-linux-arm64-v{version}.tar.gz
        checksum: sha256=eb59aee1472a4c6b81e43de7f3fb822e1da974f23e9b954911c109d34e2e4e84
    scope: system
    binaries:
      victoria-logs-prod: victoria-logs-prod
