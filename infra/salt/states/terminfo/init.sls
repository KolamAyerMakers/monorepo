/etc/terminfo:
  file.recurse:
    - user: root
    - source: salt://terminfo/files
    - dir_mode: '0755'
    - file_mode: '0644'
