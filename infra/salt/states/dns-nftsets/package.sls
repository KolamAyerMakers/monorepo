dns-nftsets::dependencies:
  pkg.installed:
    - pkgs:
      - python3-dnspython
      - python3-nftables
    - require:
      - module: apt::refresh
      - test: bootstrap::package_sources_ready
