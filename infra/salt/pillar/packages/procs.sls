packages:
  procs:
    version: 0.14.11
    arch:
      x86_64:
        libc: static
        url: https://github.com/dalance/procs/releases/download/v{version}/procs-v{version}-x86_64-linux.zip
        checksum: sha256=9c4faecf85a3af4d3d39aae47d04fa31d0a6eb0a239039f68d3f55043f04f974
      aarch64:
        libc: static
        url: https://github.com/dalance/procs/releases/download/v{version}/procs-v{version}-aarch64-linux.zip
        checksum: sha256=891855dff3143fd3620c06eb68bd63e94114dd2e369107b455d48bf60cc1464c
    scope: system
    binaries:
      - procs
