systemd-resolved::disable:
  service.dead:
    - name: systemd-resolved
    - enable: false
    - onlyif:
      - fun: service.available
        args:
          - systemd-resolved
