#!jinja|yaml|age

{% from "roles/kam-classroom/domain_helpers.sls" import https_url, ldap_base_distinguished_name, public_hostname with context %}
{% set authelia_data_directory = '/data/authelia' %}

authelia:
  paths:
    data_directory: {{ authelia_data_directory }}
    oidc_jwks_private_key_file: {{ authelia_data_directory }}/oidc_jwks_rsa_private_key.pem
    oidc_jwks_public_key_file: {{ authelia_data_directory }}/oidc_jwks_rsa_public_key.pem
  server:
    domain: {{ public_hostname }}
    path: /auth
    url: {{ https_url('auth') }}
  session:
    cookies:
      - domain: {{ public_hostname }}
        authelia_url: {{ https_url('auth') }}
  access_control:
    default_policy: deny
    rules:
      - domain: {{ public_hostname }}
        policy: one_factor
        subject: group:humans
  regulation:
    modes:
      - user
      - ip
    max_retries: 5
    find_time: 2m
    ban_time: 10m
  storage:
    local_path: {{ authelia_data_directory }}/db.sqlite3
  notifier:
    filesystem_path: {{ authelia_data_directory }}/notification.txt
  authentication_backend:
    ldap:
      address: ldap://127.0.0.1:3890
      base_dn: {{ ldap_base_distinguished_name }}
      user: uid=admin,ou=people,{{ ldap_base_distinguished_name }}
      password_pillar_key: lldap:secrets:ldap_user_pass
  identity_providers:
    oidc:
      cors:
        endpoints:
          - token
          - introspection
          - userinfo
        allowed_origins_from_client_redirect_uris: true
      authorization_policies:
        humans:
          default_policy: deny
          rules:
            - policy: one_factor
              subject: group:humans
      clients:
        - client_id: forgejo
          client_name: Forgejo
          # Digest of forgejo:oauth_sources:authelia:client_secret.
          # See pillar/roles/kam-classroom/forgejo.sls when rotating it.
          client_secret: $pbkdf2-sha512$310000$rFn6VcHA5nP9ODCAv.Y0JQ$tM2qvhDaEzoNJLPrjtmP6yNz.WSHxHLNEv9Vh8.yWz1o9ol7A4X6uw50aag0c2aC3Fttk8pzjztGS5QTwt7Wcg
          public: false
          authorization_policy: humans
          consent_mode: pre-configured
          pre_configured_consent_duration: 1 year
          require_pkce: false
          pkce_challenge_method: ''
          redirect_uris:
            - {{ https_url('git') }}user/oauth2/authelia/callback
          scopes:
            - openid
            - email
            - profile
            - groups
          response_types:
            - code
          grant_types:
            - authorization_code
          access_token_signed_response_alg: none
          userinfo_signed_response_alg: none
          token_endpoint_auth_method: client_secret_basic
        - client_id: gamja
          client_name: Gamja
          client_secret: ''
          public: true
          authorization_policy: humans
          consent_mode: pre-configured
          pre_configured_consent_duration: 1 year
          require_pkce: true
          pkce_challenge_method: S256
          redirect_uris:
            - {{ https_url('irc') }}
          scopes:
            - openid
            - profile
            - groups
          response_types:
            - code
          grant_types:
            - authorization_code
          access_token_signed_response_alg: none
          userinfo_signed_response_alg: none
          token_endpoint_auth_method: none
          introspection_endpoint_auth_method: none
  secrets:
    session_secret: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBiNEhHM05ta3RoRTBpUnk0dk1raDRteUVzbGsvdkJweFIwRVI1bXFnN0dnCjZoTW1uWVdTYVFUYUxadW51MzJOcFArendBRWs4UkdzVnIzYmw5NzEwNWsKLT4gJU4tZ3JlYXNlIC0+d110IFtlVDk2KSAhLkAgKVwKR1psbWIrSDljdHY5cGJCZ0ZUcFNVUXE4cjFEbzFiZS8zRmNmYUJ5aDQrY2V3MWJwdC90dgotLS0gUTlvalZ6RnBsK2dvYWxhZ2NzNGJEZFhWYXJGZnFMWEUvU2IzTTJBOEdZNAoqsd92qNqIJvaB9Peo0N7zPLm0w49Mjhy/YneRvqFqUs2GIty3MJCMcoBD5U/WE2Dj5lV9S4UTzD27GxRT2t9AdyiTSYuQZloUkHbAr1BYxYX8mNVdP4GcxEdgsy2K2oQ=]
    storage_encryption_key: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBtaysyQm5vZVFKY3pWZHUwWkF5QmtpdmRSUWRCK0tZbGtpRHpBTXVzS1QwCmk1YzUvczJ0K2o2L2pyRG4ycjJBNGJ4cm5RR1Y0dE5VSXBENGwyL3AvT2sKLT4gPG9SLWdyZWFzZQprT3ZYbDdFZGYyS0xqTGMveG5SNFBFS1IvZi9rcG45VWNxZkpRSHNVTjhMblRLL0ovc1lVQ0NJeGliTHE1NFVQCkp5TE9xRldjR0dvZ3J2RXRSN3VKcDRZZURnCi0tLSBxbnUwTjhtUXI2b0xsZkswVERmSjdVWmNuNG45N1NmbVdtSitMYlpsNXNzCrB/zj4i78ZF30Huf6kbGokVD2J6snTFzvhe8PWLH5ymtaKi66/Qv1Mh1fu9qc8ixSimroD0iPzlSlru97og61Vi1nvibVbiqX/ohlVCvv2nV01o4ne7dpHGxwm/1tucLw==]
    reset_password_jwt_secret: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBjYlJXVmliczhOSm1KYkp6N21Fbno4TTJaNDlVQ0dBaVVZV0padkx2VENJCldqUVlKS25HTlRpN05JUFIrYzBmck4wbDArWDdYbkJnZW9ldGVkdnplZzgKLT4gaSl+NS1ncmVhc2UgcUInLUwgYkMxCmdMcU1udS9XUjd2YkFIbG1VYVlpQTA4aWVBSzFWSmpJajhTek9tS2FWWEVJdFZxMDdYOTMyUitTb0RjCi0tLSBlTHUvRDdkZXZua1Q2bUswbGZhTENmeXJoRnZOQlcvTEdiOVNwZ0tDaXVrCptg6lgnruiEdDr7nBNbmG2Ab3i3Sc5x+qs5UsBFaTgW7VTVX6GClY2dQ9R0vu+t+tihLKIDGYFaVjkD0gHKWolh6CyrVQ0WcNHm6w7cbrrhwlG9P3J/JDceM+C0TJJQ3w==]
    oidc_hmac_secret: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSA5WWFyYkl0UjBmSk1SRk5iWkZhcTVlSzNSc21hOGxucmVNdm1tWUhKK25jCmFyYkxPb252dGVRWktzKzhsb3BkMGEzeEttZVI2b2pLazdjdzNXdG9MaTAKLT4gfngvRy1ncmVhc2UKSW5GcU1rUGVrRkRUSHhQakM1VzAvM1pLK3B1aGh3eGZYdzVTR0VtYndMckEKLS0tIGU3NkJ1SUhoYmFvWDlZQVkxd1VYdDN0Q2tXWTBuQ0xXS3U4eklvRHZHL00KouPoQLPBbM0K7+DbB1tUTwv19DaxMmbJwXmzsscfJDU6OR/cdQ5MZtb7uwLreaXRyun6/4lIUlJzUM15RbQQYTJLTddKcUsbs4DC0wMgfYodltInKyvUEbwjQH9pcGiP]
