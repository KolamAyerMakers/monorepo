include:
  - bootstrap.packages

nftables::validate:
  cmd.run:
    - name: nft -c -f /etc/nftables.conf
    - onchanges:
      - file: /etc/nftables.conf
      - file: /etc/nftables.d/*

nftables::service:
  service.running:
    - name: nftables
    - enable: true
    - require:
      - pkg: nftables
      - file: /etc/nftables.conf
      - test: bootstrap::apt_packages_ready

nftables::reload:
  cmd.run:
    - name: systemctl reload nftables
    - require:
      - service: nftables::service
    - onchanges:
      - cmd: nftables::validate
