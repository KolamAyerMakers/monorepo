packages:
  pass-otp:
    version: 1.2.0
    scope: system
    binaries: false
    strip_components: 1
    arch:
      any:
        url: https://github.com/tadfisher/pass-otp/releases/download/v{version}/pass-otp-{version}.tar.gz
        checksum: sha256=5720a649267a240a4f7ba5a6445193481070049c1d08ba38b00d20fc551c3a67
