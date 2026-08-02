packages:
  authelia:
    version: 4.39.19-glibc
    arch:
      x86_64:
        libc: glibc
        url: https://github.com/authelia/authelia/releases/download/v4.39.19/authelia-v4.39.19-linux-amd64.tar.gz
        checksum: sha256=f6f8d2450533071076f1f2bbf4abfc5b4885be0cc3565e5362bc2ac2470677a3
      aarch64:
        libc: glibc
        url: https://github.com/authelia/authelia/releases/download/v4.39.19/authelia-v4.39.19-linux-arm64.tar.gz
        checksum: sha256=9a53542ae9d1dce6d7a1cd9977fb1953fdf819eedf14422c1da736e95ecb4714
    scope: system
    binaries:
      authelia: authelia
