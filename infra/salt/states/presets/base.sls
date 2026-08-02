{% from "bootstrap/macros/packages.sls" import bootstrap_package_installed %}

include:
  - neovim
  - ripgrep
  - fd
  - lsd
  - bat
  - delta
  - starship
  - mcfly
  - tmux
  - vim
  - inputrc
  - bash
  - ssh
  - procs
  - node_exporter

{% for name, parameters in salt['pillar.get']('presets:base', {}).items() %}
{{ bootstrap_package_installed(name, parameters=parameters) }}
{% endfor %}
