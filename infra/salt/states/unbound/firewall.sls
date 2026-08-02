include:
  - unbound.package
  - nftables

{% set unbound = salt['pillar.get']('unbound', {}) %}
{% set firewall = unbound.get('firewall', {}) %}
{% set listen_address = unbound.get('listen_address') %}
{% set service_user = unbound.get('service', {}).get('user') %}
{% set forwarder_ipv4_addresses = firewall.get('forwarder_ipv4_addresses', []) %}
{% set forwarder_ipv6_addresses = firewall.get('forwarder_ipv6_addresses', []) %}
{% set forwarder_ipv4_set = forwarder_ipv4_addresses | join(', ') %}
{% set forwarder_ipv6_set = forwarder_ipv6_addresses | join(', ') %}
{% set monitoring_sources = salt['pillar.get']('firewall:nftables:policy:monitoring_sources', []) %}
{% set firewall_enabled = salt['pillar.get']('unbound:firewall:enabled') %}

unbound::firewall::enabled_required_pillar:
  test.check_pillar:
    - boolean:
      - unbound:firewall:enabled
    - failhard: true

{% if firewall_enabled %}
unbound::firewall::required_pillar:
  test.check_pillar:
    - string:
      - unbound:listen_address
      - unbound:service:user
    - integer:
      - unbound:port
    - failhard: true

unbound::firewall::dns:
  nftables_file.managed:
    - name: /etc/nftables.d/45-unbound-dns.nft
    - header: "# Unbound DNS egress policy"
    - counters:
      - output_dns
    - chains:
      - name: output
        position: '60'
    - rules:
      - chain: output
        position: '10'
        rule: ip daddr {{ listen_address }} udp dport {{ unbound.port }} counter name "output_dns" accept comment "local unbound dns udp"
      - chain: output
        position: '11'
        rule: ip daddr {{ listen_address }} tcp dport {{ unbound.port }} counter name "output_dns" accept comment "local unbound dns tcp"
      - chain: output
        position: '20'
        rule: meta skuid {{ service_user }} udp dport 53 counter name "output_dns" accept comment "recursive dns udp"
      - chain: output
        position: '21'
        rule: meta skuid {{ service_user }} tcp dport 53 counter name "output_dns" accept comment "recursive dns tcp"
{%   if forwarder_ipv4_addresses %}
      - chain: output
        position: '30'
        rule: meta skuid {{ service_user }} ip daddr { {{ forwarder_ipv4_set }} } udp dport 53 counter name "output_dns" accept comment "forwarded dns udp"
      - chain: output
        position: '31'
        rule: meta skuid {{ service_user }} ip daddr { {{ forwarder_ipv4_set }} } tcp dport 53 counter name "output_dns" accept comment "forwarded dns tcp"
{%   endif %}{# if forwarder_ipv4_addresses #}
{%   if forwarder_ipv6_addresses %}
      - chain: output
        position: '32'
        rule: meta skuid {{ service_user }} ip6 daddr { {{ forwarder_ipv6_set }} } udp dport 53 counter name "output_dns" accept comment "forwarded dns udp"
      - chain: output
        position: '33'
        rule: meta skuid {{ service_user }} ip6 daddr { {{ forwarder_ipv6_set }} } tcp dport 53 counter name "output_dns" accept comment "forwarded dns tcp"
{%   endif %}{# if forwarder_ipv6_addresses #}
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/nftables.d
      - pkg: unbound
      - test: unbound::firewall::enabled_required_pillar
      - test: unbound::firewall::required_pillar
    - watch_in:
      - cmd: nftables::validate
{% else %}
/etc/nftables.d/45-unbound-dns.nft:
  file.absent:
    - require:
      - test: unbound::firewall::enabled_required_pillar
    - watch_in:
      - cmd: nftables::validate
{% endif %}{# if firewall enabled #}

/etc/nftables.d/50-unbound-exporter.nft:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
        # Prometheus Unbound Exporter — allow metrics scraping
        # Unbound exporter reads DNS resolver statistics from Unbound's
        # remote-control interface (TCP 127.0.0.1:8953) and exposes them
        # as Prometheus metrics on port 9167. Access is restricted to
        # monitoring_sources (VictoriaMetrics scraper).
        #
        # The resolver path itself is managed in /etc/nftables.d/45-unbound-dns.nft.
        table inet filter {
        {% for source in monitoring_sources %}
        {%   set key = source | replace('.', '_') | replace('/', '_') %}
            counter input_unbound_exp_{{ key }} {}
        {% endfor %}{# for source in monitoring_sources #}
            chain input {
        {% for source in monitoring_sources %}
        {%   set key = source | replace('.', '_') | replace('/', '_') %}
                ip saddr {{ source }} tcp dport 9167 counter name "input_unbound_exp_{{ key }}" accept comment "unbound exporter from {{ source }}"
        {% endfor %}{# for source in monitoring_sources #}
            }
        }
    - require:
      - file: /etc/nftables.d
    - watch_in:
      - cmd: nftables::validate
