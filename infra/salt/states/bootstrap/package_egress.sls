{% set package_egress = salt['pillar.get']('bootstrap:package_egress', {}) %}
{% set enabled = package_egress.get('enabled', false) %}
{% set manage_resolv_conf = salt['pillar.get']('unbound:manage_resolv_conf', false) %}

bootstrap::package_egress::required_pillar:
  test.check_pillar:
    - boolean:
      - bootstrap:package_egress:enabled
    - listing:
      - bootstrap:package_egress:users
      - bootstrap:package_egress:nameservers
      - bootstrap:package_egress:dns_ports
      - bootstrap:package_egress:http_ports
    - failhard: true

bootstrap::package_egress:
  cmd.script:
    - name: salt://bootstrap/files/package-egress.sh.j2
    - template: jinja
    - require:
      - test: bootstrap::package_egress::required_pillar
    - unless: |
        if [ "{{ enabled | lower }}" != "true" ]; then
          exit 0
        fi
{% if manage_resolv_conf %}
        if ! grep -Eq '^nameserver[[:space:]]+127[.]0[.]0[.]1$' /etc/resolv.conf; then
          exit 1
        fi
{% endif %}
        if ! nft list chain inet filter output >/dev/null 2>&1; then
          exit 0
        fi

        nft list chain inet filter output | grep -Fq "temporary bootstrap package egress"
