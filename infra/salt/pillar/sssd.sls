sssd:
  enabled: false
  configuration_file: /etc/sssd/sssd.conf
  configuration_directory: /etc/sssd
  domain_configuration_directory: /etc/sssd/conf.d
  services:
    - nss
    - pam
    - ssh
  nss:
    filter_users:
      - root
    filter_groups:
      - root
  pam:
    offline_failed_login_attempts: 3
    offline_failed_login_delay: 5
  domains: {}
  nsswitch:
    passwd: files systemd sss
    group: files systemd sss
    shadow: files sss
    gshadow: files sss
    hosts: files myhostname dns
    networks: files
    protocols: db files
    services: db files
    ethers: db files
    rpc: db files
    netgroup: files sss
  pam_auth_update:
    enabled_profiles:
      - sss
      - mkhomedir
