packages:
  i3-battery-popup:
    version: 1.1.1
    arch:
      any:
        url: https://github.com/rjekker/i3-battery-popup/archive/refs/tags/v{version}.tar.gz
        checksum: sha256=b37af2f62be5f7a484b873bd3cecf2373eecbeeb98b65125cb4aaecb1cb18a98
    scope: system
    binaries:
      - i3-battery-popup
    strip_components: 1
