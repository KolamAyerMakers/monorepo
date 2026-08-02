{% set lookup_table = salt['pillar.get']('openssh-server:lookup') %}
{% set data = salt['grains.filter_by'](lookup_table) %}
{{ data['service'] }}:
  service.running:
    - enable: true
    - require:
      - pkg: openssh-server
    - watch:
      - pkg: openssh-server
      - file: /etc/ssh/sshd_config
