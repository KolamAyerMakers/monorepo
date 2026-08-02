rsyslog:
  service:
    name: rsyslog
    main_configuration_file: /etc/rsyslog.conf
    local_default_configuration_file: /etc/rsyslog.d/50-default.conf
    configuration_file: /etc/rsyslog.d/50-victorialogs-forward.conf
    queue_spool_directory: /var/spool/rsyslog
    queue_spool_user: root
    queue_spool_group: root
    log_file_owner: root
    log_file_group: adm
    log_file_create_mode: '0640'
    log_directory_create_mode: '0755'
    umask: '0022'
  victorialogs_forward:
    enabled: false
    local_hostname: "{{ grains.id }}"
    port: 514
    protocol: tcp
    template: RSYSLOG_SyslogProtocol23Format
    source_name_map_file: /etc/rsyslog.d/syslog-source-names.json
    imjournal:
      state_file: imjournal-victorialogs.state
      persist_state_interval: 100
      ignore_previous_messages: true
      file_create_mode: '0640'
    queue:
      type: LinkedList
      filename: victorialogs_forward
      size: 100000
      high_watermark: 80000
      low_watermark: 20000
      max_disk_space: 1g
      save_on_shutdown: true
  receiver:
    enabled: false
    tcp_listen_port: 514
    udp_listen_port: 514
    source_name_map: {}
