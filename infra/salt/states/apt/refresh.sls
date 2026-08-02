include:
- apt.sources

apt::refresh:
  module.wait:
    - name: pkg.refresh_db
    - require:
      - sls: apt.sources
    - order: 20
