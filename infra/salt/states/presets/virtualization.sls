{% from "bootstrap/macros/packages.sls" import bootstrap_package_installed %}

include:
  - nftables

{% for name, parameters in salt['pillar.get']('presets:virtualization', {}).items() %}
{{ bootstrap_package_installed(name, parameters=parameters) }}
{% endfor %}

/etc/nftables.d/40-development-virtual-machines.nft:
  file.managed:
    - source: salt://presets/templates/development-virtual-machines.nft.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/nftables.d
    - watch_in:
      - cmd: nftables::validate
