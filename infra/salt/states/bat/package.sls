{% from "bootstrap/macros/packages.sls" import bootstrap_binary_package %}

include:
  - github.download_egress

bat::apt::remove:
  pkg.removed:
    - name: bat

{{ bootstrap_binary_package('bat', extra_requirements=['pkg: bat::apt::remove']) }}
