include:
  - nftables

{% set firewall = salt['pillar.get']('dhcp-client:firewall', {}) %}

{% if firewall.get('enabled', true) %}
nftables::dhcp_client:
  nftables_file.managed:
    - name: /etc/nftables.d/20-dhcp-client.nft
    - header: "# DHCP client firewall policy"
    - counters:
      - input_dhcp_client
      - output_dhcp_client
    - chains:
      - name: input
        position: '50'
      - name: output
        position: '60'
    - rules:
      - chain: input
        position: '10'
        rule: udp sport 67 udp dport 68 counter name "input_dhcp_client" accept comment "dhcpv4 client"
      - chain: input
        position: '20'
        rule: udp sport 547 udp dport 546 counter name "input_dhcp_client" accept comment "dhcpv6 client"
      - chain: output
        position: '10'
        rule: udp sport 68 udp dport 67 counter name "output_dhcp_client" accept comment "dhcpv4 client"
      - chain: output
        position: '20'
        rule: udp sport 546 udp dport 547 counter name "output_dhcp_client" accept comment "dhcpv6 client"
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/nftables.d
    - watch_in:
      - cmd: nftables::validate
{% else %}
/etc/nftables.d/20-dhcp-client.nft:
  file.absent:
    - watch_in:
      - cmd: nftables::validate
{% endif %}
