include:
  - authelia.package

{% set authelia = salt['pillar.get']('authelia', {}) %}
{% set service = authelia.get('service', {}) %}
{% set paths = authelia.get('paths', {}) %}
{% set server = authelia.get('server', {}) %}
{% set session = authelia.get('session', {}) %}
{% set access_control = authelia.get('access_control', {}) %}
{% set regulation = authelia.get('regulation', {}) %}
{% set storage = authelia.get('storage', {}) %}
{% set notifier = authelia.get('notifier', {}) %}
{% set authentication_backend = authelia.get('authentication_backend', {}) %}
{% set ldap = authentication_backend.get('ldap', {}) %}
{% set identity_providers = authelia.get('identity_providers', {}) %}
{% set oidc = identity_providers.get('oidc', {}) %}
{% set oidc_clients = oidc.get('clients', []) %}
{% set oidc_enabled = oidc_clients | length > 0 %}
{% set secrets = authelia.get('secrets', {}) %}
{% set ldap_password = salt['pillar.get'](ldap.get('password_pillar_key', 'authelia:authentication_backend:ldap:password'), '') %}
{% set secret_values = {
    'session_secret': secrets.get('session_secret', ''),
    'storage_encryption_key': secrets.get('storage_encryption_key', ''),
    'reset_password_jwt_secret': secrets.get('reset_password_jwt_secret', ''),
    'ldap_password': ldap_password,
    'oidc_hmac_secret': secrets.get('oidc_hmac_secret', ''),
} %}

authelia::configuration::required_pillar:
  test.check_pillar:
    - string:
      - authelia:service:user
      - authelia:service:group
      - authelia:service:shell
      - authelia:service:home
      - authelia:service:unit_file
      - authelia:paths:configuration_directory
      - authelia:paths:configuration_file
      - authelia:paths:data_directory
      - authelia:paths:secrets_directory
      - authelia:paths:secret_environment_file
      - authelia:paths:session_secret_file
      - authelia:paths:storage_encryption_key_file
      - authelia:paths:reset_password_jwt_secret_file
      - authelia:paths:ldap_password_file
{% if oidc_enabled %}
      - authelia:paths:oidc_hmac_secret_file
      - authelia:paths:oidc_jwks_private_key_file
      - authelia:paths:oidc_jwks_public_key_file
{% endif %}
      - authelia:server:domain
      - authelia:server:host
      - authelia:server:path
      - authelia:server:url
{% if not session.get('cookies') %}
      - authelia:session:cookie_domain
{% endif %}{# if not session.get('cookies') #}
      - authelia:access_control:default_policy
{% if regulation %}
      - authelia:regulation:find_time
      - authelia:regulation:ban_time
{% endif %}
      - authelia:storage:local_path
      - authelia:notifier:filesystem_path
      - authelia:authentication_backend:ldap:implementation
      - authelia:authentication_backend:ldap:address
      - authelia:authentication_backend:ldap:base_dn
      - authelia:authentication_backend:ldap:user
      - authelia:authentication_backend:ldap:password_pillar_key
      - authelia:secrets:session_secret
      - authelia:secrets:storage_encryption_key
      - authelia:secrets:reset_password_jwt_secret
{% if oidc_enabled %}
      - authelia:secrets:oidc_hmac_secret
{% endif %}
{% if oidc_enabled %}
    - dictionary:
      - authelia:identity_providers:oidc
{% if oidc.get('authorization_policies') %}
{%   for policy_name, policy in oidc.get('authorization_policies', {}).items() %}
      - authelia:identity_providers:oidc:authorization_policies:{{ policy_name }}
{%   endfor %}
{% endif %}
{% if oidc.get('cors') %}
      - authelia:identity_providers:oidc:cors
{% endif %}
{% endif %}
{% if oidc.get('cors', {}).get('endpoints') %}
    - listing:
      - authelia:identity_providers:oidc:cors:endpoints
{% endif %}
{% if session.get('cookies') %}
    - listing:
      - authelia:session:cookies
{% endif %}{# if session.get('cookies') #}
{% if regulation %}
    - listing:
      - authelia:regulation:modes
{% endif %}
    - integer:
      - authelia:service:uid
      - authelia:service:gid
      - authelia:server:port
{% if regulation %}
      - authelia:regulation:max_retries
{% endif %}
    - boolean:
      - authelia:service:system_user
      - authelia:service:create_home
      - authelia:authentication_backend:password_reset_disable
      - authelia:authentication_backend:password_change_disable
    - failhard: true

authelia::group:
  group.present:
    - name: {{ service.group }}
    - system: true
    - gid: {{ service.gid }}
    - require:
      - test: authelia::configuration::required_pillar

authelia::user:
  user.present:
    - name: {{ service.user }}
    - system: {{ service.system_user | yaml }}
    - uid: {{ service.uid }}
    - shell: {{ service.shell }}
    - home: {{ service.home }}
    - createhome: {{ service.create_home | yaml }}
    - gid: {{ service.group }}
    - require:
      - group: authelia::group
      - test: authelia::configuration::required_pillar

authelia::data_directory:
  file.directory:
    - name: {{ paths.data_directory }}
    - user: {{ service.user }}
    - group: {{ service.group }}
    - mode: '0750'
    - makedirs: true
    - require:
      - user: authelia::user
      - test: authelia::configuration::required_pillar

authelia::configuration_directory:
  file.directory:
    - name: {{ paths.configuration_directory }}
    - user: root
    - group: {{ service.group }}
    - mode: '0750'
    - makedirs: true
    - require:
      - user: authelia::user
      - test: authelia::configuration::required_pillar

authelia::secrets_directory:
  file.directory:
    - name: {{ paths.secrets_directory }}
    - user: root
    - group: {{ service.group }}
    - mode: '0750'
    - makedirs: true
    - require:
      - file: authelia::configuration_directory
      - test: authelia::configuration::required_pillar

authelia::session_secret_file:
  file.managed:
    - name: {{ paths.session_secret_file }}
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - contents: |
        {{ secret_values.session_secret | trim }}
    - require:
      - file: authelia::secrets_directory
      - test: authelia::configuration::required_pillar

authelia::storage_encryption_key_file:
  file.managed:
    - name: {{ paths.storage_encryption_key_file }}
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - contents: |
        {{ secret_values.storage_encryption_key | trim }}
    - require:
      - file: authelia::secrets_directory
      - test: authelia::configuration::required_pillar

authelia::reset_password_jwt_secret_file:
  file.managed:
    - name: {{ paths.reset_password_jwt_secret_file }}
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - contents: |
        {{ secret_values.reset_password_jwt_secret | trim }}
    - require:
      - file: authelia::secrets_directory
      - test: authelia::configuration::required_pillar

authelia::ldap_password_file:
  file.managed:
    - name: {{ paths.ldap_password_file }}
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - contents: |
        {{ secret_values.ldap_password | trim }}
    - require:
      - file: authelia::secrets_directory
      - test: authelia::configuration::required_pillar

{% if oidc_enabled %}
authelia::oidc_hmac_secret_file:
  file.managed:
    - name: {{ paths.oidc_hmac_secret_file }}
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - contents: |
        {{ secret_values.oidc_hmac_secret | trim }}
    - require:
      - file: authelia::secrets_directory
      - test: authelia::configuration::required_pillar

authelia::oidc_jwks_key_pair:
  cmd.run:
    - name: >-
        /usr/local/bin/authelia crypto pair rsa generate
        --directory {{ paths.data_directory }}
        --file.private-key oidc_jwks_rsa_private_key.pem
        --file.public-key oidc_jwks_rsa_public_key.pem
    - unless: test -s {{ paths.oidc_jwks_private_key_file }}
    - require:
      - packages: authelia
      - file: authelia::data_directory
      - test: authelia::configuration::required_pillar

authelia::oidc_jwks_private_key_file:
  file.managed:
    - name: {{ paths.oidc_jwks_private_key_file }}
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - replace: false
    - require:
      - cmd: authelia::oidc_jwks_key_pair
      - test: authelia::configuration::required_pillar

authelia::oidc_jwks_public_key_file:
  file.managed:
    - name: {{ paths.oidc_jwks_public_key_file }}
    - user: root
    - group: {{ service.group }}
    - mode: '0644'
    - replace: false
    - require:
      - cmd: authelia::oidc_jwks_key_pair
      - test: authelia::configuration::required_pillar

{% endif %}
authelia::secret_environment_file:
  file.managed:
    - name: {{ paths.secret_environment_file }}
    - source: salt://authelia/templates/authelia.env.j2
    - template: jinja
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - context:
        paths: {{ paths | yaml }}
        oidc_enabled: {{ oidc_enabled | yaml }}
    - require:
      - file: authelia::secrets_directory
      - file: authelia::session_secret_file
      - file: authelia::storage_encryption_key_file
      - file: authelia::reset_password_jwt_secret_file
      - file: authelia::ldap_password_file
{% if oidc_enabled %}
      - file: authelia::oidc_hmac_secret_file
{% endif %}
      - test: authelia::configuration::required_pillar

{{ paths.configuration_file }}:
  file.managed:
    - source: salt://authelia/templates/configuration.yml.j2
    - template: jinja
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - context:
        server: {{ server | yaml }}
        session: {{ session | yaml }}
        access_control: {{ access_control | yaml }}
        regulation: {{ regulation | yaml }}
        storage: {{ storage | yaml }}
        notifier: {{ notifier | yaml }}
        authentication_backend: {{ authentication_backend | yaml }}
        identity_providers: {{ identity_providers | yaml }}
        paths: {{ paths | yaml }}
    - require:
      - file: authelia::configuration_directory
      - file: authelia::data_directory
      - file: authelia::secret_environment_file
{% if oidc_enabled %}
      - file: authelia::oidc_jwks_private_key_file
      - file: authelia::oidc_jwks_public_key_file
{% endif %}
      - test: authelia::configuration::required_pillar
