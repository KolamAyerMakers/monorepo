{% from "bootstrap/macros/packages.sls" import bootstrap_binary_package, bootstrap_package_installed %}

include:
  - github.download_egress

{% set package_directory = '/opt/packages/ergo' %}
{% set package_version = salt['pillar.get']('packages:ergo:version') %}
{% set package_architecture = {
    'x86_64': 'x86_64',
    'amd64': 'x86_64',
    'aarch64': 'arm64',
    'arm64': 'arm64',
}.get(salt['grains.get']('cpuarch'), salt['grains.get']('cpuarch')) %}
{% set versioned_language_directory = package_directory ~ '/ergo-' ~ package_version ~ '-linux-' ~ package_architecture ~ '/languages' %}

{{ bootstrap_package_installed('openssl', state_identifier='ergo::openssl') }}

{{ bootstrap_package_installed('ldap-utils', state_identifier='ergo::ldap_utils') }}

{{ bootstrap_binary_package(
    'ergo',
    parameters=[
      {'strip_components': 1},
    ]
) }}

ergo::languages_directory_compatibility_symlink:
  file.symlink:
    - name: {{ package_directory }}/languages
    - target: {{ versioned_language_directory }}
    - onlyif: test ! -d {{ package_directory }}/languages -a -d {{ versioned_language_directory }}
    - require:
      - packages: ergo
