{%- from "bootstrap/macros/packages.sls" import bootstrap_package_installed -%}

include:
  - bootstrap.packages

{{ bootstrap_package_installed('toilet', state_identifier='roles::kam_classroom::toilet') }}

{{ bootstrap_package_installed('lolcat', state_identifier='roles::kam_classroom::lolcat') }}

/usr/local/bin/kolam-makers-logo:
  file.managed:
    - source: salt://roles/kam-classroom/files/kolam_makers_logo.sh
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - pkg: roles::kam_classroom::toilet
      - pkg: roles::kam_classroom::lolcat

/etc/update-motd.d:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'

/etc/update-motd.d/10-kolam-makers-logo:
  file.symlink:
    - target: /usr/local/bin/kolam-makers-logo
    - user: root
    - group: root
    - mode: '0755'
    - force: true
    - require:
      - file: /usr/local/bin/kolam-makers-logo
      - file: /etc/update-motd.d

roles::kam_classroom::kolam_makers_logo::clear_stale_motd_cache:
  cmd.run:
    - name: rm -f /run/motd.dynamic && install -D -m 0644 /usr/local/bin/kolam-makers-logo /var/lib/kam-classroom/kolam-makers-logo.motd-cache-version
    - unless: cmp -s /usr/local/bin/kolam-makers-logo /var/lib/kam-classroom/kolam-makers-logo.motd-cache-version
    - require:
      - file: /usr/local/bin/kolam-makers-logo
      - file: /etc/update-motd.d/10-kolam-makers-logo
