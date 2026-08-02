include:
  - forgejo.package

{% set forgejo = salt['pillar.get']('forgejo', {}) %}
{% set app_name = forgejo.get('app_name', '') %}
{% set service = forgejo.get('service', {}) %}
{% set paths = forgejo.get('paths', {}) %}
{% set server = forgejo.get('server', {}) %}
{% set registration = forgejo.get('registration', {}) %}
{% set oauth2_client = forgejo.get('oauth2_client', {}) %}

forgejo::config::required_pillar:
  test.check_pillar:
    - string:
      - forgejo:app_name
      - forgejo:service:user
      - forgejo:service:group
      - forgejo:service:shell
      - forgejo:service:home
      - forgejo:service:unit_file
      - forgejo:paths:configuration_directory
      - forgejo:paths:configuration_file
      - forgejo:paths:ssh_directory
      - forgejo:paths:secret_directory
      - forgejo:paths:secret_key_file
      - forgejo:paths:internal_token_file
      - forgejo:paths:lfs_jwt_secret_file
      - forgejo:paths:oauth2_jwt_secret_file
      - forgejo:paths:data_directory
      - forgejo:paths:log_directory
      - forgejo:server:domain
      - forgejo:server:root_url
      - forgejo:server:http_address
      - forgejo:server:ssh_domain
      - forgejo:server:landing_page
      - forgejo:server:logout_redirect
      - forgejo:oauth2_client:account_linking
      - forgejo:oauth2_client:username
    - integer:
      - forgejo:server:http_port
      - forgejo:server:ssh_port
    - boolean:
      - forgejo:service:system_user
      - forgejo:service:create_home
      - forgejo:registration:disable_registration
      - forgejo:registration:allow_only_external_registration
      - forgejo:registration:show_registration_button
      - forgejo:registration:enable_internal_signin
      - forgejo:registration:openid_signin_enabled
      - forgejo:registration:openid_signup_enabled
      - forgejo:oauth2_client:enable_auto_registration
    - listing:
      - forgejo:registration:openid_whitelisted_uris
    - failhard: true

forgejo::group:
  group.present:
    - name: {{ service.group }}
    - system: true
    - require:
      - test: forgejo::config::required_pillar

forgejo::user:
  user.present:
    - name: {{ service.user }}
    - system: {{ service.system_user | yaml }}
    - shell: {{ service.shell }}
    - home: {{ service.home }}
    - createhome: {{ service.create_home | yaml }}
    - gid: {{ service.group }}
    - require:
      - group: forgejo::group
      - test: forgejo::config::required_pillar

forgejo::data_directory:
  file.directory:
    - name: {{ paths.data_directory }}
    - user: {{ service.user }}
    - group: {{ service.group }}
    - mode: '0750'
    - makedirs: true
    - require:
      - user: forgejo::user
      - test: forgejo::config::required_pillar

forgejo::log_directory:
  file.directory:
    - name: {{ paths.log_directory }}
    - user: {{ service.user }}
    - group: {{ service.group }}
    - mode: '0750'
    - makedirs: true
    - require:
      - user: forgejo::user
      - test: forgejo::config::required_pillar

forgejo::ssh_directory:
  file.directory:
    - name: {{ paths.ssh_directory }}
    - user: {{ service.user }}
    - group: {{ service.group }}
    - mode: '0700'
    - makedirs: true
    - require:
      - user: forgejo::user
      - test: forgejo::config::required_pillar

forgejo::secret_directory:
  file.directory:
    - name: {{ paths.secret_directory }}
    - user: root
    - group: {{ service.group }}
    - mode: '0770'
    - makedirs: true
    - require:
      - file: forgejo::data_directory
      - test: forgejo::config::required_pillar

forgejo::configuration_directory:
  file.directory:
    - name: {{ paths.configuration_directory }}
    - user: root
    - group: {{ service.group }}
    - mode: '0770'
    - makedirs: true
    - require:
      - user: forgejo::user
      - test: forgejo::config::required_pillar

forgejo::obsolete_custom_footer_template:
  file.absent:
    - name: {{ paths.data_directory }}/custom/templates/custom/footer.tmpl
    - require:
      - test: forgejo::config::required_pillar

forgejo::obsolete_head_navbar_template:
  file.absent:
    - name: {{ paths.data_directory }}/custom/templates/base/head_navbar.tmpl
    - require:
      - test: forgejo::config::required_pillar

forgejo::secret_key:
  cmd.run:
    - name: >-
        umask 0077 &&
        /usr/local/bin/forgejo generate secret SECRET_KEY > {{ paths.secret_key_file }} &&
        chown root:{{ service.group }} {{ paths.secret_key_file }} &&
        chmod 0640 {{ paths.secret_key_file }}
    - unless: test -s {{ paths.secret_key_file }}
    - require:
      - packages: forgejo
      - file: forgejo::secret_directory
      - test: forgejo::config::required_pillar

forgejo::internal_token:
  cmd.run:
    - name: >-
        umask 0077 &&
        /usr/local/bin/forgejo generate secret INTERNAL_TOKEN > {{ paths.internal_token_file }} &&
        chown root:{{ service.group }} {{ paths.internal_token_file }} &&
        chmod 0640 {{ paths.internal_token_file }}
    - unless: test -s {{ paths.internal_token_file }}
    - require:
      - packages: forgejo
      - file: forgejo::secret_directory
      - test: forgejo::config::required_pillar

forgejo::lfs_jwt_secret:
  cmd.run:
    - name: >-
        umask 0077 &&
        /usr/local/bin/forgejo generate secret LFS_JWT_SECRET > {{ paths.lfs_jwt_secret_file }} &&
        chown root:{{ service.group }} {{ paths.lfs_jwt_secret_file }} &&
        chmod 0640 {{ paths.lfs_jwt_secret_file }}
    - unless: test -s {{ paths.lfs_jwt_secret_file }}
    - require:
      - packages: forgejo
      - file: forgejo::secret_directory
      - test: forgejo::config::required_pillar

forgejo::oauth2_jwt_secret:
  cmd.run:
    - name: >-
        umask 0077 &&
        /usr/local/bin/forgejo generate secret JWT_SECRET > {{ paths.oauth2_jwt_secret_file }} &&
        chown root:{{ service.group }} {{ paths.oauth2_jwt_secret_file }} &&
        chmod 0640 {{ paths.oauth2_jwt_secret_file }}
    - unless: test -s {{ paths.oauth2_jwt_secret_file }}
    - require:
      - packages: forgejo
      - file: forgejo::secret_directory
      - test: forgejo::config::required_pillar

{{ paths.configuration_file }}:
  file.managed:
    - source: salt://forgejo/templates/app.ini.j2
    - template: jinja
    - user: root
    - group: {{ service.group }}
    - mode: '0660'
    - context:
        app_name: {{ app_name | yaml }}
        service: {{ service | yaml }}
        paths: {{ paths | yaml }}
        server: {{ server | yaml }}
        registration: {{ registration | yaml }}
        oauth2_client: {{ oauth2_client | yaml }}
    - require:
      - file: forgejo::configuration_directory
      - file: forgejo::data_directory
      - file: forgejo::log_directory
      - file: forgejo::ssh_directory
      - cmd: forgejo::secret_key
      - cmd: forgejo::internal_token
      - cmd: forgejo::lfs_jwt_secret
      - cmd: forgejo::oauth2_jwt_secret
      - test: forgejo::config::required_pillar
