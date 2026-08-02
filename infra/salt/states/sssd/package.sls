{% from "bootstrap/macros/packages.sls" import bootstrap_package_installed %}

{{ bootstrap_package_installed('sssd', state_identifier='sssd::package') }}

{{ bootstrap_package_installed('sssd-tools') }}

{{ bootstrap_package_installed('libnss-sss') }}

{{ bootstrap_package_installed('libpam-sss') }}

{{ bootstrap_package_installed('libsss-sudo') }}
