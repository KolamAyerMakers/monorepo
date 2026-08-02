{% from "bootstrap/macros/packages.sls" import bootstrap_package_installed with context %}

{{ bootstrap_package_installed(
  pillar_key='systemd-timesyncd:package',
  state_identifier='systemd-timesyncd::package',
) }}
