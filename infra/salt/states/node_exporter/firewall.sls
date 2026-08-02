include:
  - nftables

{%- set monitoring_sources = salt['pillar.get']('firewall:nftables:policy:monitoring_sources', []) %}

/etc/nftables.d/50-node-exporter.nft:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
        # Prometheus Node Exporter — allow metrics scraping
        # Node exporter exposes system metrics (CPU, memory, disk, network)
        # on port 9100. Access is restricted to monitoring_sources
        # (VictoriaMetrics scraper) to prevent information disclosure
        # to arbitrary network clients.
        table inet filter {
{% for source in monitoring_sources %}
{%- set key = source | replace('.', '_') | replace('/', '_') %}
            counter input_node_exp_{{ key }} {}
{% endfor %}{# for source in monitoring_sources #}
            chain input {
{% for source in monitoring_sources %}
{%- set key = source | replace('.', '_') | replace('/', '_') %}
                ip saddr {{ source }} tcp dport 9100 counter name "input_node_exp_{{ key }}" accept comment "node exporter from {{ source }}"
{% endfor %}{# for source in monitoring_sources #}
            }
        }
    - require:
      - file: /etc/nftables.d
    - watch_in:
      - cmd: nftables::validate
