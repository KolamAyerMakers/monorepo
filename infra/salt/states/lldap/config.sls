include:
  - lldap.package

{% set lldap = salt['pillar.get']('lldap', {}) %}
{% set service = lldap.get('service', {}) %}
{% set paths = lldap.get('paths', {}) %}
{% set ldap = lldap.get('ldap', {}) %}
{% set http = lldap.get('http', {}) %}
{% set secrets = lldap.get('secrets', {}) %}

lldap::configuration::required_pillar:
  test.check_pillar:
    - string:
      - lldap:service:user
      - lldap:service:group
      - lldap:service:shell
      - lldap:service:home
      - lldap:service:unit_file
      - lldap:paths:configuration_directory
      - lldap:paths:configuration_file
      - lldap:paths:data_directory
      - lldap:paths:secret_environment_file
      - lldap:paths:assets_directory
      - lldap:ldap:host
      - lldap:ldap:base_dn
      - lldap:ldap:user_dn
      - lldap:ldap:user_email
      - lldap:http:domain
      - lldap:http:host
      - lldap:http:url
      - lldap:secrets:jwt_secret
      - lldap:secrets:ldap_user_pass
      - lldap:secrets:key_seed
    - integer:
      - lldap:service:uid
      - lldap:service:gid
      - lldap:ldap:port
      - lldap:http:port
    - boolean:
      - lldap:service:system_user
      - lldap:service:create_home
    - failhard: true

lldap::group:
  group.present:
    - name: {{ service.group }}
    - system: true
    - gid: {{ service.gid }}
    - require:
      - test: lldap::configuration::required_pillar

lldap::user:
  user.present:
    - name: {{ service.user }}
    - system: {{ service.system_user | yaml }}
    - uid: {{ service.uid }}
    - shell: {{ service.shell }}
    - home: {{ service.home }}
    - createhome: {{ service.create_home | yaml }}
    - gid: {{ service.group }}
    - require:
      - group: lldap::group
      - test: lldap::configuration::required_pillar

lldap::data_directory:
  file.directory:
    - name: {{ paths.data_directory }}
    - user: {{ service.user }}
    - group: {{ service.group }}
    - mode: '0750'
    - makedirs: true
    - require:
      - user: lldap::user
      - test: lldap::configuration::required_pillar

lldap::configuration_directory:
  file.directory:
    - name: {{ paths.configuration_directory }}
    - user: root
    - group: {{ service.group }}
    - mode: '0750'
    - makedirs: true
    - require:
      - user: lldap::user
      - test: lldap::configuration::required_pillar

lldap::secret_environment_file:
  file.managed:
    - name: {{ paths.secret_environment_file }}
    - source: salt://lldap/templates/lldap.env.j2
    - template: jinja
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - context:
        secrets: {{ secrets | yaml }}
    - require:
      - file: lldap::configuration_directory
      - test: lldap::configuration::required_pillar

{{ paths.configuration_file }}:
  file.managed:
    - source: salt://lldap/templates/lldap_config.toml.j2
    - template: jinja
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - context:
        paths: {{ paths | yaml }}
        ldap: {{ ldap | yaml }}
        http: {{ http | yaml }}
    - require:
      - file: lldap::configuration_directory
      - file: lldap::data_directory
      - file: lldap::secret_environment_file
      - test: lldap::configuration::required_pillar
