include:
  - authelia.config

{% set authelia = salt['pillar.get']('authelia', {}) %}
{% set service = authelia.get('service', {}) %}
{% set paths = authelia.get('paths', {}) %}
{% set identity_providers = authelia.get('identity_providers', {}) %}
{% set oidc = identity_providers.get('oidc', {}) %}
{% set oidc_enabled = oidc.get('clients', []) | length > 0 %}

authelia::service::required_pillar:
  test.check_pillar:
    - string:
      - authelia:service:user
      - authelia:service:group
      - authelia:service:home
      - authelia:service:unit_file
      - authelia:paths:configuration_file
      - authelia:paths:data_directory
      - authelia:paths:secret_environment_file
    - failhard: true

authelia::unit_file:
  file.managed:
    - name: {{ service.unit_file }}
    - source: salt://authelia/templates/authelia.service.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        service: {{ service | yaml }}
        paths: {{ paths | yaml }}
    - require:
      - test: authelia::service::required_pillar

authelia::systemd_daemon_reload:
  module.run:
    - service.systemctl_reload: []
    - onchanges:
      - file: authelia::unit_file

authelia::service:
  service.running:
    - name: authelia
    - enable: true
    - require:
      - packages: authelia
      - file: {{ paths.configuration_file }}
      - file: authelia::data_directory
      - file: authelia::secret_environment_file
      - file: authelia::unit_file
      - module: authelia::systemd_daemon_reload
      - test: authelia::service::required_pillar
    - watch:
      - packages: authelia
      - file: {{ paths.configuration_file }}
      - file: authelia::secret_environment_file
      - file: authelia::session_secret_file
      - file: authelia::storage_encryption_key_file
      - file: authelia::reset_password_jwt_secret_file
      - file: authelia::ldap_password_file
{% if oidc_enabled %}
      - file: authelia::oidc_hmac_secret_file
      - cmd: authelia::oidc_jwks_key_pair
      - file: authelia::oidc_jwks_private_key_file
      - file: authelia::oidc_jwks_public_key_file
{% endif %}
      - file: authelia::unit_file
