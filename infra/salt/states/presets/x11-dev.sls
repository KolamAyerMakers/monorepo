{% from "bootstrap/macros/packages.sls" import bootstrap_package_installed %}

include:
  - presets.cli-dev
  - appearance
  - i3
  - kitty
  - polybar
  - rofi
  - fonts
  - xprofile
  - xresources
  - pass
  - gdb

{% for name, parameters in salt['pillar.get']('presets:x11', {}).items() %}
{{ bootstrap_package_installed(name, parameters=parameters) }}
{% endfor %}
