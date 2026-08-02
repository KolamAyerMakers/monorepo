{% set github = salt['pillar.get']('github', {}) %}
{% set download_egress = github.get('download_egress', {}) %}
{% set enabled = download_egress.get('enabled', true) %}
{% set dns_nftsets = salt['pillar.get']('dns-nftsets', {}) %}
{% set dns_nftsets_configuration = dns_nftsets.get('configuration', {}) %}
{% set user = download_egress.user %}
{% set tcp_port = download_egress.tcp_port %}
{% set set_v4 = download_egress.set_v4 %}
{% set set_v6 = download_egress.set_v6 %}
{% set counter = 'output_github_downloads' %}
{% set comment = 'github downloads' %}

{% if enabled %}
include:
  - dns-nftsets.configuration
  - dns-nftsets.service
  - nftables

github::download_egress::required_pillar:
  test.check_pillar:
    - boolean:
      - github:download_egress:enabled
    - string:
      - github:download_egress:nftables_file
      - github:download_egress:header
      - github:download_egress:destination
      - github:download_egress:set_v4
      - github:download_egress:set_v6
      - github:download_egress:destination_position
      - github:download_egress:domain_position
      - github:download_egress:user
      - dns-nftsets:configuration:path
      - dns-nftsets:configuration:set_timeout
    - integer:
      - github:download_egress:tcp_port
    - listing:
      - github:download_egress:domains
    - failhard: true

github::download_egress::dns_nftsets:
  dns_nftsets.fragment:
    - target: {{ dns_nftsets_configuration.path }}
    - destination_position: {{ download_egress.destination_position }}
    - domain_position: {{ download_egress.domain_position }}
    - destinations:
        {{ download_egress.destination }}:
          family: inet
          table: filter
          set_v4: {{ download_egress.set_v4 }}
          set_v6: {{ download_egress.set_v6 }}
    - domains:
{% for domain in download_egress.get('domains', []) %}
      - exact: {{ domain }}
        destination: {{ download_egress.destination }}
{% endfor %}{# for domain in download_egress.get('domains', []) #}
    - require_in:
      - concat: dns-nftsets::configuration_file
    - require:
      - test: github::download_egress::required_pillar

github::download_egress:
  nftables_file.managed:
    - name: {{ download_egress.nftables_file }}
    - header: "{{ download_egress.header }}"
    - counters:
      - output_github_downloads
    - sets:
      - name: {{ download_egress.set_v4 }}
        type: ipv4_addr
        flags:
          - timeout
        timeout: {{ dns_nftsets_configuration.set_timeout }}
        position: '25'
      - name: {{ download_egress.set_v6 }}
        type: ipv6_addr
        flags:
          - timeout
        timeout: {{ dns_nftsets_configuration.set_timeout }}
        position: '25'
    - chains:
      - name: output
        position: '60'
    - rules:
      - chain: output
        position: '10'
        rule: meta skuid {{ user }} ip daddr @{{ set_v4 }} tcp dport {{ tcp_port }} counter name "{{ counter }}" accept comment "{{ comment }}"
      - chain: output
        position: '11'
        rule: meta skuid {{ user }} ip6 daddr @{{ set_v6 }} tcp dport {{ tcp_port }} counter name "{{ counter }}" accept comment "{{ comment }}"
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/nftables.d
      - test: github::download_egress::required_pillar
    - watch_in:
      - cmd: nftables::validate

github::download_egress::ready:
  test.nop:
    - name: github download egress ready
    - require:
      - cmd: dns-nftsets::service
      - dns_nftsets: github::download_egress::dns_nftsets
      - nftables_file: github::download_egress
{% else %}
github::download_egress::required_pillar:
  test.check_pillar:
    - boolean:
      - github:download_egress:enabled
    - failhard: true

github::download_egress::ready:
  test.nop:
    - name: github download egress disabled
    - require:
      - test: github::download_egress::required_pillar
{% endif %}
