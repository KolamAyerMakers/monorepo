include:
  - nftables

{% set tcp_ports = salt['pillar.get']('nftables:ingress:tcp_ports') %}

nftables::ingress::required_pillar:
  test.check_pillar:
    - listing:
      - nftables:ingress:tcp_ports
    - failhard: true

{% if tcp_ports %}
/etc/nftables.d/50-ingress.nft:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
        # Host ingress ports
        table inet filter {
            counter input_ingress_tcp {}
            chain input {
                tcp dport { {{ tcp_ports | join(', ') }} } counter name "input_ingress_tcp" accept comment "host tcp ingress"
            }
        }
    - require:
      - file: /etc/nftables.d
      - test: nftables::ingress::required_pillar
    - watch_in:
      - cmd: nftables::validate
{% else %}
/etc/nftables.d/50-ingress.nft:
  file.absent:
    - require:
      - test: nftables::ingress::required_pillar
    - watch_in:
      - cmd: nftables::validate
{% endif %}{# if tcp_ports #}
