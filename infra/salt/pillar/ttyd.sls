ttyd:
  service:
    user: ttyd
    group: ttyd
    uid: 984
    gid: 978
    shell: /usr/sbin/nologin
    home: /var/lib/ttyd
    system_user: true
    create_home: false
    unit_directory: /etc/systemd/system
    protect_clock: true
    protect_kernel_logs: true
    restrict_realtime: true
    system_call_architectures: native
  instances: {}
