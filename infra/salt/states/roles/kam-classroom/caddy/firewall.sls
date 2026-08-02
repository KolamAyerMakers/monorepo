include:
  - nftables

{% set caddy = salt['pillar.get']('caddy', {}) %}

kam-classroom::caddy::firewall::required_pillar:
  test.check_pillar:
    - string:
      - caddy:service_user
    - integer:
      - caddy:http_port
      - caddy:https_port
    - failhard: true

kam-classroom::caddy::firewall:
  nftables_file.managed:
    - name: /etc/nftables.d/50-kam-classroom-caddy.nft
    - header: "# Kolam Ayer Makers classroom Caddy HTTP and HTTPS policy"
    - counters:
      - input_kam_classroom_caddy
      - output_kam_classroom_caddy_acme
    - chains:
      - name: input
        position: '50'
      - name: output
        position: '50'
    - rules:
      - chain: input
        position: '10'
        rule: >-
          tcp dport { {{ caddy.http_port }}, {{ caddy.https_port }} }
          counter name "input_kam_classroom_caddy" accept comment "kolam ayer makers classroom caddy http https"
      - chain: output
        position: '10'
        rule: >-
          meta skuid {{ caddy.service_user }} tcp dport { {{ caddy.http_port }}, {{ caddy.https_port }} }
          counter name "output_kam_classroom_caddy_acme" accept comment "kolam ayer makers classroom caddy acme"
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/nftables.d
      - test: kam-classroom::caddy::firewall::required_pillar
    - watch_in:
      - cmd: nftables::validate
