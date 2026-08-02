include:
  - roles.kam-classroom.packages

/var/lib/tldr:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - makedirs: true

/var/lib/tldr/.tldrrc:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
        {
          "cache": "/var/cache/tldr",
          "platform": "linux",
          "skipUpdateWhenPageNotFound": true
        }
    - require:
      - file: /var/lib/tldr

/var/cache/tldr:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - makedirs: true

/usr/local/bin/tldr:
  file.managed:
    - user: root
    - group: root
    - mode: '0755'
    - follow_symlinks: false
    - contents: |
        #!/bin/sh
        export DOTENV_CONFIG_QUIET=true
        unset NODE_OPTIONS
        export HOME=/var/lib/tldr
        exec /opt/packages/nodejs/bin/tldr "$@"
    - require:
      - cmd: nodejs::npm_global::tldr::install
      - file: /var/lib/tldr/.tldrrc

roles::kam_classroom::tldr::cache:
  cmd.run:
    - name: timeout 120s env HOME=/var/lib/tldr DOTENV_CONFIG_QUIET=true /opt/packages/nodejs/bin/tldr --update || true
    - creates: /var/cache/tldr/cache/shortIndex.json
    - require:
      - cmd: nodejs::npm_global::tldr::install
      - file: /var/cache/tldr
      - file: /var/lib/tldr/.tldrrc

/etc/profile.d/dotenvx_quiet.sh:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
        export DOTENV_CONFIG_QUIET=true
