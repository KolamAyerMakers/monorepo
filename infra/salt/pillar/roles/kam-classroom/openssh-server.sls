{% from "roles/kam-classroom/domain_helpers.sls" import https_url, public_hostname with context %}
{% set registration_command = [
  '/usr/bin/sudo',
  '/usr/local/bin/maker-guide-registration check',
  '&& exec',
  '/usr/local/bin/maker-guide-register',
  '--fully-qualified-domain-name ' ~ public_hostname,
  '--login-host ' ~ public_hostname,
  '--web-ssh-url ' ~ https_url('ssh'),
] | join(' ') %}

openssh-server:
  config:
    PasswordAuthentication: 'no'
    KbdInteractiveAuthentication: 'no'
    ChallengeResponseAuthentication: 'no'
    AllowUsers: null
    AuthorizedKeysFile: .ssh/authorized_keys
    AuthorizedKeysCommand: /usr/bin/sss_ssh_authorizedkeys
    AuthorizedKeysCommandUser: nobody
    PermitRootLogin: prohibit-password
    ExposeAuthInfo: 'yes'
    PermitEmptyPasswords: 'no'
    PermitTTY: 'yes'
    DisableForwarding: 'yes'
    MaxAuthTries: 3
    LoginGraceTime: 20
    MaxStartups: '3:30:10'
    MaxSessions: 2
    Match:
      - condition: User new
        options:
          AuthenticationMethods: none
          PermitEmptyPasswords: 'yes'
          PasswordAuthentication: 'yes'
          ForceCommand: {{ registration_command }}
      - condition: User git
        options:
          AuthorizedKeysFile: /data/forgejo/ssh/authorized_keys
          AuthenticationMethods: publickey
      - condition: Group linux-foundations
        options:
          AuthenticationMethods: any
          PasswordAuthentication: 'yes'
  firewall:
    allowed_source_ipv4_prefixes:
      - 0.0.0.0/0
    allowed_source_ipv6_prefixes:
      - "::/0"
