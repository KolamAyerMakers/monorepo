authelia:
  service:
    user: authelia
    group: authelia
    uid: 987
    gid: 981
    shell: /usr/sbin/nologin
    home: /nonexistent
    system_user: true
    create_home: false
    unit_file: /etc/systemd/system/authelia.service
  paths:
    configuration_directory: /etc/authelia
    configuration_file: /etc/authelia/configuration.yml
    data_directory: /var/lib/authelia
    secrets_directory: /etc/authelia/secrets
    secret_environment_file: /etc/authelia/authelia.env
    session_secret_file: /etc/authelia/secrets/session_secret
    storage_encryption_key_file: /etc/authelia/secrets/storage_encryption_key
    reset_password_jwt_secret_file: /etc/authelia/secrets/reset_password_jwt_secret
    ldap_password_file: /etc/authelia/secrets/ldap_password
    oidc_hmac_secret_file: /etc/authelia/secrets/oidc_hmac_secret
    oidc_jwks_private_key_file: /var/lib/authelia/oidc_jwks_rsa_private_key.pem
    oidc_jwks_public_key_file: /var/lib/authelia/oidc_jwks_rsa_public_key.pem
  server:
    domain: localhost
    host: 127.0.0.1
    port: 9091
    path: /
    url: http://localhost:9091/
  session:
    cookie_domain: localhost
  access_control:
    default_policy: one_factor
  regulation:
    modes:
      - user
      - ip
    max_retries: 5
    find_time: 2m
    ban_time: 10m
  storage:
    local_path: /var/lib/authelia/db.sqlite3
  notifier:
    filesystem_path: /var/lib/authelia/notification.txt
  authentication_backend:
    password_reset_disable: false
    password_change_disable: false
    ldap:
      implementation: lldap
      address: ldap://127.0.0.1:3890
      base_dn: dc=example,dc=com
      user: uid=admin,ou=people,dc=example,dc=com
      password_pillar_key: authelia:authentication_backend:ldap:password
  identity_providers:
    oidc:
      clients: []
