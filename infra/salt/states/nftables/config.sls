/etc/nftables.d:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - pkg: nftables

/etc/nftables.conf:
  file.managed:
    - source: salt://nftables/templates/nftables.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - pkg: nftables
      - file: /etc/nftables.d
