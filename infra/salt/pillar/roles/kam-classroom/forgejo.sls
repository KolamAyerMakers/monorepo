#!jinja|yaml|age

{% from "roles/kam-classroom/domain_helpers.sls" import https_url, public_hostname with context %}
{% set forgejo_data_directory = '/data/forgejo' %}
{% set forgejo_secret_directory = forgejo_data_directory ~ '/secrets' %}
{% set forgejo_ssh_directory = forgejo_data_directory ~ '/ssh' %}

forgejo:
  app_name: Kolam Ayer Makers Forgejo
  paths:
    ssh_directory: {{ forgejo_ssh_directory }}
    secret_directory: {{ forgejo_secret_directory }}
    secret_key_file: {{ forgejo_secret_directory }}/secret_key
    internal_token_file: {{ forgejo_secret_directory }}/internal_token
    lfs_jwt_secret_file: {{ forgejo_secret_directory }}/lfs_jwt_secret
    oauth2_jwt_secret_file: {{ forgejo_secret_directory }}/oauth2_jwt_secret
    data_directory: {{ forgejo_data_directory }}
  server:
    domain: {{ public_hostname }}
    root_url: {{ https_url('git') }}
    ssh_domain: {{ public_hostname }}
    landing_page: /git/user/oauth2/authelia
    logout_redirect: /git/.kam-classroom/logout
  registration:
    disable_registration: true
    allow_only_external_registration: true
    show_registration_button: false
    enable_internal_signin: false
    openid_signup_enabled: true
    openid_whitelisted_uris:
      - {{ public_hostname }}
  oauth2_client:
    enable_auto_registration: true
    account_linking: auto
    username: nickname
  oauth_sources:
    authelia:
      provider: openidConnect
      client_id: forgejo
      client_secret_file: {{ forgejo_secret_directory }}/oauth_authelia_client_secret
      # Plaintext for the digest in
      # authelia:identity_providers:oidc:clients:forgejo:client_secret.
      # See pillar/roles/kam-classroom/authelia.sls when rotating it.
      client_secret: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBZbUpCcTIzYTJpM1JDenJtckdzQ05ycWVYNjV4Qm5MMDZTVTlBUHUxa0JBCkp1bWFtZUk4VFdJMFBVRldIemNwbEY3aGF0dis1Y3llWGpVdjA1NitDdzQKLT4gekB1QUV2LWdyZWFzZSB3JzAjIGIgSX1TRSNbdzIgX1kjCndrTllDYXk4YVRTNWVkZ3N6bGRzCi0tLSBBc09YNEVaSUdBcVN5VXNRNHNJRHNEMmliWEtja05qT2QxNG1Ga3cxV05VCgYeG38PozjAAqMxAvCtxAzLsPSuU5l+MLk0ThFmXeW+wQYTsxLSDIQZxSPyOXz/b0ZiLSez2CRfBq0C5pv0Jo4AkPZMWaa3zPf05x2KAdXz/E92LClx72ikoRRMs+PlyQ==]
      auto_discover_url: {{ https_url('auth') }}.well-known/openid-configuration
      scopes:
        - openid
        - email
        - profile
        - groups
      group_claim_name: groups
      skip_local_2fa: true
      require:
        - host: roles::kam_classroom::hosts::service_domains
        - service: authelia::service
        - service: kam-classroom::caddy::service
