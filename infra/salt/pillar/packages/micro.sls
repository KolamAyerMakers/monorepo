packages:
  micro:
    version: 2.0.15
    arch:
      x86_64:
        url: https://github.com/micro-editor/micro/releases/download/v{version}/micro-{version}-linux64.tar.gz
        checksum: sha256=dfa1b6ae53e4e0b063b54224fd2b6b0a3c3159ea09d042a3a8f5cd001844d44c
      aarch64:
        url: https://github.com/micro-editor/micro/releases/download/v{version}/micro-{version}-linux-arm64.tar.gz
        checksum: sha256=5ca127857bf5500be3879f1a70b27556e737a49da04a1be5334de9e8e8781ad9
    scope: system
    binaries:
      - micro
    strip_components: 1
