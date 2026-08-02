include:
  - apt.refresh
  - bootstrap.package_egress

bootstrap::package_sources_ready:
  test.nop:
    - require:
      - cmd: bootstrap::package_egress

bootstrap::apt_packages_ready:
  test.nop:
    - require:
      - test: bootstrap::package_sources_ready

extend:
  apt::refresh:
    module.wait:
      - require:
        - cmd: bootstrap::package_egress
