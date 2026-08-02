openssh-server:
  lookup:
    Debian:
      service: ssh
    RedHat:
      service: sshd
  config:
    Port: 22
    ListenAddress:
      - 0.0.0.0
      - "::"
    # Salt-SSH deploys thin archives through OpenSSH scp, which uses SFTP by
    # default on modern OpenSSH releases. Keep this enabled or Salt-SSH cannot
    # deploy thin on managed hosts.
    Subsystem: sftp /usr/lib/openssh/sftp-server
    KbdInteractiveAuthentication: 'no'
    ChallengeResponseAuthentication: 'no'
    PasswordAuthentication: 'no'
    # Keep PAM account checks enabled. The root shadow password is set to "!"
    # to disable password login; disabling PAM here makes OpenSSH reject
    # public-key root logins after sshd reload.
    UsePAM: 'yes'
    AuthenticationMethods: publickey
    PubkeyAuthentication: 'yes'
    AllowUsers: root
    IgnoreRhosts: 'yes'
    HostbasedAuthentication: 'no'
    X11Forwarding: 'no'
    PrintMotd: 'no'
    TCPKeepAlive: 'yes'
    ClientAliveInterval: 60
    ClientAliveCountMax: 3
    UseDNS: 'yes'
    PermitRootLogin: prohibit-password
    MaxAuthTries: 3
    LoginGraceTime: 20
    MaxStartups: '3:30:10'
    MaxSessions: 2
    LogLevel: VERBOSE
