{% from "bootstrap/macros/packages.sls" import bootstrap_binary_package, bootstrap_package_installed %}

include:
  - github.download_egress

{{ bootstrap_package_installed('git', state_identifier='forgejo::git') }}

{{ bootstrap_package_installed('git-lfs', state_identifier='forgejo::git_lfs') }}

{{ bootstrap_binary_package('forgejo') }}
