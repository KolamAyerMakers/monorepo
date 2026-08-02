forgejo:
  app_name: Forgejo
  service:
    user: git
    group: git
    shell: /bin/bash
    home: /home/git
    system_user: true
    create_home: true
    unit_file: /etc/systemd/system/forgejo.service
  paths:
    configuration_directory: /etc/forgejo
    configuration_file: /etc/forgejo/app.ini
    ssh_directory: /home/git/.ssh
    secret_directory: /etc/forgejo
    secret_key_file: /etc/forgejo/secret_key
    internal_token_file: /etc/forgejo/internal_token
    lfs_jwt_secret_file: /etc/forgejo/lfs_jwt_secret
    oauth2_jwt_secret_file: /etc/forgejo/oauth2_jwt_secret
    data_directory: /var/lib/forgejo
    log_directory: /var/log/forgejo
  server:
    http_address: 127.0.0.1
    http_port: 3000
    ssh_port: 22
    landing_page: home
    logout_redirect: ''
  registration:
    disable_registration: true
    allow_only_external_registration: false
    show_registration_button: true
    enable_internal_signin: true
    openid_signin_enabled: false
    openid_signup_enabled: false
    openid_whitelisted_uris: []
  oauth2_client:
    enable_auto_registration: false
    account_linking: login
    username: nickname
  oauth_sources: {}
