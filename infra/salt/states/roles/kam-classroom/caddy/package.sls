{% from "bootstrap/macros/packages.sls" import bootstrap_package_installed %}

{{ bootstrap_package_installed(
  pillar_key='caddy:package',
  state_identifier='kam-classroom::caddy::package',
) }}
