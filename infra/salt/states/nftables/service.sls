include:
  - bootstrap.packages

nftables::validate:
  cmd.run:
    - name: nft -c -f /etc/nftables.conf
    - require:
      - test: bootstrap::apt_packages_ready
    - onchanges:
      - file: /etc/nftables.conf
      # Match file and nftables_file names without requiring either fragment type.
      - /etc/nftables.d/*

# A stopped service must validate even when Salt reports no file changes.
nftables::validate_startup:
  cmd.run:
    - name: nft -c -f /etc/nftables.conf
    - unless: systemctl is-active --quiet nftables
    - require:
      - cmd: nftables::validate

nftables::service:
  service.running:
    - name: nftables
    - enable: true
    - require:
      - pkg: nftables
      - file: /etc/nftables.conf
      - test: bootstrap::apt_packages_ready
      - cmd: nftables::validate_startup

nftables::reload:
  cmd.run:
    - name: systemctl reload nftables
    - require:
      - service: nftables::service
    - onchanges:
      - cmd: nftables::validate
