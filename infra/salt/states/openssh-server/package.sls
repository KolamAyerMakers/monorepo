{% from "bootstrap/macros/packages.sls" import bootstrap_package_installed %}

{{ bootstrap_package_installed('openssh-server', parameters=['version: latest']) }}
