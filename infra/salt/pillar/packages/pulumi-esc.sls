packages:
  pulumi-esc:
    version: 0.23.0
    arch:
      x86_64:
        url: https://github.com/pulumi/esc/releases/download/v{version}/esc-v{version}-linux-x64.tar.gz
        checksum: sha256=72c1499df5f9472169f180a408ab7c6728a66532370a44d24523e2d722fdfb07
    scope: system
    binaries:
      - esc
    bin_subdir: bin
    strip_components: 1
