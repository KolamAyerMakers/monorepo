include:
  - nftables.config
  - nftables.service

{%- set monitoring_sources = salt['pillar.get']('firewall:nftables:policy:monitoring_sources', []) %}

/etc/nftables.d/50-nftables-exporter.nft:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
        # Prometheus nftables Exporter — allow metrics scraping
        # nftables-exporter reads counter data via nft and exposes them
        # as Prometheus metrics on port 9630. Access is restricted to
        # monitoring_sources (VictoriaMetrics scraper).
        table inet filter {
{% for source in monitoring_sources %}
{%- set key = source | replace('.', '_') | replace('/', '_') %}
            counter input_nftables_exp_{{ key }} {}
{% endfor %}{# for source in monitoring_sources #}
            chain input {
{% for source in monitoring_sources %}
{%- set key = source | replace('.', '_') | replace('/', '_') %}
                ip saddr {{ source }} tcp dport 9630 counter name "input_nftables_exp_{{ key }}" accept comment "nftables exporter from {{ source }}"
{% endfor %}{# for source in monitoring_sources #}
            }
        }
    - require:
      - file: /etc/nftables.d
    - watch_in:
      - cmd: nftables::validate
