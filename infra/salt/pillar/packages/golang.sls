packages:
  golang:
    version: 1.24.13
    arch:
      x86_64:
        url: https://go.dev/dl/go{version}.linux-amd64.tar.gz
        checksum: sha256=1fc94b57134d51669c72173ad5d49fd62afb0f1db9bf3f798fd98ee423f8d730
      aarch64:
        url: https://go.dev/dl/go{version}.linux-arm64.tar.gz
        checksum: sha256=74d97be1cc3a474129590c67ebf748a96e72d9f3a2b6fef3ed3275de591d49b3
    scope: system
    binaries:
      - go
      - gofmt
    bin_subdir: bin
    strip_components: 1
