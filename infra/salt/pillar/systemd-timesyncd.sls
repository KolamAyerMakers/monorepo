systemd-timesyncd:
  package: systemd-timesyncd
  service:
    name: systemd-timesyncd
    user: systemd-timesync
  config:
    ntp:
      - pool.ntp.org
    fallback_ntp: []
  firewall:
    destination: systemd-timesyncd-ntp
    set_v4: systemd_timesyncd_ntp_v4
    set_v6: systemd_timesyncd_ntp_v6
    port: 123
