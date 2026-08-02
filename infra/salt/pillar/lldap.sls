lldap:
  service:
    user: lldap
    group: lldap
    uid: 992
    gid: 982
    shell: /usr/sbin/nologin
    home: /nonexistent
    system_user: true
    create_home: false
    unit_file: /etc/systemd/system/lldap.service
  paths:
    configuration_directory: /etc/lldap
    configuration_file: /etc/lldap/lldap_config.toml
    data_directory: /var/lib/lldap
    secret_environment_file: /etc/lldap/lldap.env
    assets_directory: /opt/packages/lldap/app
  ldap:
    host: 127.0.0.1
    port: 3890
    base_dn: dc=example,dc=com
    user_dn: admin
    user_email: ''
  http:
    domain: localhost
    host: 127.0.0.1
    port: 17170
    url: http://localhost:17170/
