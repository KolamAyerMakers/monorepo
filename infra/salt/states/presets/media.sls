{% from "bootstrap/macros/packages.sls" import bootstrap_package_installed %}

{% for name, parameters in salt['pillar.get']('presets:media', {}).items() %}
{{ bootstrap_package_installed(name, parameters=parameters) }}
{% endfor %}
