systemd:
  drop_ins:
    session_policy:
      drop_in_directory: /etc/systemd/logind.conf.d
      drop_in_file: /etc/systemd/logind.conf.d/80-session-policy.conf
      configuration:
        Login:
          KillUserProcesses: 'yes'
          UserStopDelaySec: 0
          RemoveIPC: 'yes'
          UserTasksMax: 128
          RuntimeDirectorySize: 256M
          SessionsMax: 256
      service: systemd-logind
    resource_limits:
      drop_in_directory: /etc/systemd/system/user-.slice.d
      drop_in_file: /etc/systemd/system/user-.slice.d/80-resource-limits.conf
      configuration:
        Slice:
          TasksAccounting: 'yes'
          TasksMax: 128
          MemoryAccounting: 'yes'
          MemoryMax: 1G
          MemorySwapMax: 256M
          CPUAccounting: 'yes'
          CPUQuota: 100%
          IOAccounting: 'yes'
      daemon_reload: true
