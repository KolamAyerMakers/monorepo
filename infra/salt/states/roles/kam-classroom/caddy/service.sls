include:
  - roles.kam-classroom.caddy.config
  - roles.kam-classroom.caddy.firewall

{% set caddy = salt['pillar.get']('caddy', {}) %}

kam-classroom::caddy::service::required_pillar:
  test.check_pillar:
    - string:
      - caddy:configuration_file
    - boolean:
      - caddy:local_certs
    - failhard: true

kam-classroom::caddy::service:
  service.running:
    - name: caddy
    - enable: true
    - require:
      - pkg: kam-classroom::caddy::package
      - file: {{ caddy.configuration_file }}
      - nftables_file: kam-classroom::caddy::firewall
      - cmd: kam-classroom::caddy::configuration::validate
      - cmd: nftables::reload
      - service: forgejo::service
      - service: lldap::service
      - service: ttyd::instance::registration::service
      - service: ttyd::instance::ssh::service
      - test: kam-classroom::caddy::service::required_pillar
    - watch:
      - file: {{ caddy.configuration_file }}
      - pkg: kam-classroom::caddy::package

{% if caddy.get('local_certs', False) %}
kam-classroom::caddy::local_ca_trusted:
  cmd.run:
    - name: |
        set -eu
        source_certificate=/var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt
        destination_certificate=/usr/local/share/ca-certificates/caddy-local-root.crt
        elapsed_seconds=0
        while [ ! -s "$source_certificate" ]; do
            if [ "$elapsed_seconds" -ge 60 ]; then
                echo "Timed out waiting for $source_certificate" >&2
                exit 1
            fi
            sleep 2
            elapsed_seconds=$((elapsed_seconds + 2))
        done
        install -m 0644 "$source_certificate" "$destination_certificate"
        update-ca-certificates
    - unless: cmp -s /var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt /usr/local/share/ca-certificates/caddy-local-root.crt
    - require:
      - service: kam-classroom::caddy::service
      - test: kam-classroom::caddy::service::required_pillar
{% endif %}
