include:
  - dns-nftsets.configuration
  - dns-nftsets.service
  - nftables

{% set weather = salt['pillar.get']('kam_classroom:weather_egress', {}) %}
{% set dns_nftsets = salt['pillar.get']('dns-nftsets', {}) %}
{% set dns_configuration = dns_nftsets.get('configuration', {}) %}
{% set humans_gid = salt['pillar.get']('kam_classroom:identity:groups:humans:gid_number') %}

roles::kam_classroom::weather::required_pillar:
  test.check_pillar:
    - string:
      - dns-nftsets:configuration:path
      - dns-nftsets:configuration:set_timeout
      - kam_classroom:weather_egress:nftables_file
      - kam_classroom:weather_egress:header
      - kam_classroom:weather_egress:destination
      - kam_classroom:weather_egress:set_v4
      - kam_classroom:weather_egress:set_v6
      - kam_classroom:weather_egress:destination_position
      - kam_classroom:weather_egress:domain_position
    - integer:
      - kam_classroom:weather_egress:tcp_port
      - kam_classroom:identity:groups:humans:gid_number
    - listing:
      - kam_classroom:weather_egress:domains
    - failhard: true

roles::kam_classroom::weather::dns_nftsets:
  dns_nftsets.fragment:
    - target: {{ dns_configuration.path }}
    - destination_position: {{ weather.destination_position }}
    - domain_position: {{ weather.domain_position }}
    - destinations:
        {{ weather.destination }}:
          family: inet
          table: filter
          set_v4: {{ weather.set_v4 }}
          set_v6: {{ weather.set_v6 }}
    - domains:
{% for domain in weather.get('domains', []) %}
      - exact: {{ domain }}
        destination: {{ weather.destination }}
{% endfor %}{# for domain in weather.get('domains', []) #}
    - require_in:
      - concat: dns-nftsets::configuration_file
    - require:
      - test: roles::kam_classroom::weather::required_pillar

roles::kam_classroom::weather:
  nftables_file.managed:
    - name: {{ weather.nftables_file }}
    - header: "{{ weather.header }}"
    - counters:
      - output_classroom_weather
    - sets:
      - name: {{ weather.set_v4 }}
        type: ipv4_addr
        flags:
          - timeout
        timeout: {{ dns_configuration.set_timeout }}
        position: '25'
      - name: {{ weather.set_v6 }}
        type: ipv6_addr
        flags:
          - timeout
        timeout: {{ dns_configuration.set_timeout }}
        position: '25'
    - chains:
      - name: output
        position: '60'
    - rules:
      - chain: output
        position: '10'
        rule: >-
          meta skgid {{ humans_gid }} ip daddr @{{ weather.set_v4 }}
          tcp dport {{ weather.tcp_port }} counter name "output_classroom_weather"
          accept comment "classroom weather APIs"
      - chain: output
        position: '11'
        rule: >-
          meta skgid {{ humans_gid }} ip6 daddr @{{ weather.set_v6 }}
          tcp dport {{ weather.tcp_port }} counter name "output_classroom_weather"
          accept comment "classroom weather APIs"
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/nftables.d
      - test: roles::kam_classroom::weather::required_pillar
    - require_in:
      - cmd: dns-nftsets::service
    - onchanges_in:
      - cmd: nftables::reload
    - watch_in:
      - cmd: nftables::validate
