{% set packages = salt['pillar.get']('pam_pwquality:packages', []) %}

pam-pwquality::packages::required_pillar:
  test.check_pillar:
    - listing:
      - pam_pwquality:packages
    - failhard: true

pam-pwquality::packages:
  pkg.installed:
    - pkgs: {{ packages | yaml }}
    - require:
      - module: apt::refresh
      - test: bootstrap::package_sources_ready
      - test: pam-pwquality::packages::required_pillar
    - require_in:
      - test: bootstrap::apt_packages_ready
