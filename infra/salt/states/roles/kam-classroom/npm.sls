include:
  - roles.kam-classroom.bot
  - dns-nftsets.configuration
  - dns-nftsets.service
  - nftables

{% set npm_egress = salt['pillar.get']('kam_classroom:npm_egress', {}) %}
{% set dns_nftsets = salt['pillar.get']('dns-nftsets', {}) %}
{% set configuration = dns_nftsets.get('configuration', {}) %}

roles::kam_classroom::npm::required_pillar:
  test.check_pillar:
    - string:
      - dns-nftsets:configuration:path
      - dns-nftsets:configuration:set_timeout
      - kam_classroom:npm_egress:nftables_file
      - kam_classroom:npm_egress:header
      - kam_classroom:npm_egress:destination
      - kam_classroom:npm_egress:set_v4
      - kam_classroom:npm_egress:set_v6
      - kam_classroom:npm_egress:destination_position
      - kam_classroom:npm_egress:domain_position
      - kam_classroom:npm_egress:user
    - integer:
      - kam_classroom:npm_egress:gid
      - kam_classroom:npm_egress:tcp_port
    - listing:
      - kam_classroom:npm_egress:domains
    - failhard: true

roles::kam_classroom::npm::dns_nftsets:
  dns_nftsets.fragment:
    - target: {{ configuration.path }}
    - destination_position: {{ npm_egress.destination_position }}
    - domain_position: {{ npm_egress.domain_position }}
    - destinations:
        {{ npm_egress.destination }}:
          family: inet
          table: filter
          set_v4: {{ npm_egress.set_v4 }}
          set_v6: {{ npm_egress.set_v6 }}
    - domains:
{% for domain in npm_egress.get('domains', []) %}
      - exact: {{ domain }}
        destination: {{ npm_egress.destination }}
{% endfor %}{# for domain in npm_egress.get('domains', []) #}
    - require_in:
      - concat: dns-nftsets::configuration_file
    - require:
      - test: roles::kam_classroom::npm::required_pillar

roles::kam_classroom::npm:
  nftables_file.managed:
    - name: {{ npm_egress.nftables_file }}
    - header: "{{ npm_egress.header }}"
    - counters:
      - output_classroom_npm
    - sets:
      - name: {{ npm_egress.set_v4 }}
        type: ipv4_addr
        flags:
          - timeout
        timeout: {{ configuration.set_timeout }}
        position: '25'
      - name: {{ npm_egress.set_v6 }}
        type: ipv6_addr
        flags:
          - timeout
        timeout: {{ configuration.set_timeout }}
        position: '25'
    - chains:
      - name: output
        position: '60'
    - rules:
      - chain: output
        position: '10'
        rule: >-
          meta skgid {{ npm_egress.gid }} ip daddr @{{ npm_egress.set_v4 }}
          tcp dport {{ npm_egress.tcp_port }} counter name "output_classroom_npm"
          accept comment "classroom npm registry"
      - chain: output
        position: '11'
        rule: >-
          meta skgid {{ npm_egress.gid }} ip6 daddr @{{ npm_egress.set_v6 }}
          tcp dport {{ npm_egress.tcp_port }} counter name "output_classroom_npm"
          accept comment "classroom npm registry"
      - chain: output
        position: '12'
        rule: >-
          meta skuid {{ npm_egress.user }} ip daddr @{{ npm_egress.set_v4 }}
          tcp dport {{ npm_egress.tcp_port }} counter name "output_classroom_npm"
          accept comment "classroom npm registry"
      - chain: output
        position: '13'
        rule: >-
          meta skuid {{ npm_egress.user }} ip6 daddr @{{ npm_egress.set_v6 }}
          tcp dport {{ npm_egress.tcp_port }} counter name "output_classroom_npm"
          accept comment "classroom npm registry"
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/nftables.d
      - test: roles::kam_classroom::npm::required_pillar
      - user: roles::kam_classroom::bot::user
    - require_in:
      - cmd: dns-nftsets::service
    - onchanges_in:
      - cmd: nftables::reload
    - watch_in:
      - cmd: nftables::validate
