packages:
  pulumi:
    version: 3.229.0
    arch:
      x86_64:
        url: https://github.com/pulumi/pulumi/releases/download/v{version}/pulumi-v{version}-linux-x64.tar.gz
        checksum: sha256=72bd77f5d2536fd46ee99c87e8bd71a8440908b5c6fdb0007faedb0d4e6488f1
    scope: system
    binaries:
      - pulumi
    bin_subdir: bin
    strip_components: 1
