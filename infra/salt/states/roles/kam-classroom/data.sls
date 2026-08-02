/data:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - makedirs: true
    - require_in:
      - file: forgejo::data_directory
      - file: lldap::data_directory
      - file: authelia::data_directory
