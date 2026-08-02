{% from "bootstrap/macros/packages.sls" import bootstrap_binary_package %}

include:
  - github.download_egress

{{ bootstrap_binary_package('ripgrep') }}
