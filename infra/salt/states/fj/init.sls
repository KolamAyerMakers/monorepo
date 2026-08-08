include:
  - fj.package

fj::fallback_host::required_pillar:
  test.check_pillar:
    - string:
      - forgejo:server:root_url
    - failhard: true

/etc/profile.d/fj.sh:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
        export FJ_FALLBACK_HOST="{{ salt['pillar.get']('forgejo:server:root_url') }}"
    - require:
      - packages: fj
      - test: fj::fallback_host::required_pillar
