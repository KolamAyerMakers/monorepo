{%- from "bootstrap/macros/packages.sls" import bootstrap_package_installed -%}

include:
  - bootstrap.packages
  - nftables

{% set traceroute = salt['pillar.get']('kam_classroom:network_diagnostics:traceroute', {}) %}

kam-classroom::network-diagnostics::required-pillar:
  test.check_pillar:
    - string:
      - kam_classroom:network_diagnostics:traceroute:firewall_file
      - kam_classroom:network_diagnostics:traceroute:udp_port_range
    - integer:
      - kam_classroom:identity:groups:humans:gid_number
    - listing:
      - kam_classroom:network_diagnostics:packages
    - failhard: true

{% for package in salt['pillar.get']('kam_classroom:network_diagnostics:packages', []) %}
{{ bootstrap_package_installed(
    package,
    state_identifier='kam-classroom::network-diagnostics::' ~ package,
    extra_requirements=[{'test': 'kam-classroom::network-diagnostics::required-pillar'}],
) }}
{% endfor %}

kam-classroom::network-diagnostics::traceroute-firewall:
  nftables_file.managed:
    - name: {{ traceroute.firewall_file }}
    - header: "# Kolam Ayer Makers classroom traceroute egress policy"
    - counters:
      - output_kam_classroom_traceroute
    - chains:
      - name: output
        position: '50'
    - rules:
      - chain: output
        position: '10'
        rule: >-
          meta skgid {{ salt['pillar.get']('kam_classroom:identity:groups:humans:gid_number') }} udp dport {{ traceroute.udp_port_range }}
          counter name "output_kam_classroom_traceroute" accept comment "classroom users traceroute udp"
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/nftables.d
      - test: kam-classroom::network-diagnostics::required-pillar
    - watch_in:
      - cmd: nftables::validate
