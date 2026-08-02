packages:
  age:
    version: 1.3.1
    arch:
      x86_64:
        url: https://github.com/FiloSottile/age/releases/download/v{version}/age-v{version}-linux-amd64.tar.gz
        checksum: sha256=bdc69c09cbdd6cf8b1f333d372a1f58247b3a33146406333e30c0f26e8f51377
    scope: system
    binaries:
      - age
      - age-keygen
    strip_components: 1
