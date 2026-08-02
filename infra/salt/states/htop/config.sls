htop::config:
  file.managed:
    - name: /etc/htoprc
    - mode: '0644'
    - user: 'root'
    - group: 'root'
    - source: salt://htop/files/htoprc
