{% from "bootstrap/macros/packages.sls" import bootstrap_binary_package %}

include:
  - github.download_egress

lsd::apt::remove:
  pkg.removed:
    - name: lsd

{{ bootstrap_binary_package('lsd', extra_requirements=['pkg: lsd::apt::remove']) }}
