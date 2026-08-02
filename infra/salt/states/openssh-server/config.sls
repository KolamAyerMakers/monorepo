/etc/ssh/sshd_config:
  file.managed:
    - source: salt://openssh-server/templates/sshd_config.j2
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - context:
        config: {{ salt['pillar.get']('openssh-server:config')|yaml }}
    - require:
      - pkg: openssh-server
