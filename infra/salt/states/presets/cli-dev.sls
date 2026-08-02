{% from "bootstrap/macros/packages.sls" import bootstrap_package_installed %}

include:
  - presets.base
  - claude-code
  - d2
  - golang
  - golangci-lint
  - fnm
  - uv
  - just
  - rtk
  - tree-sitter
  - git
  - nodejs
  - fx
  - fzf
  - micro
  - presenterm
  - glow

{% for name, parameters in salt['pillar.get']('presets:development', {}).items() %}
{{ bootstrap_package_installed(name, parameters=parameters) }}
{% endfor %}
