include:
  - ergo.package

{% set ergo = salt['pillar.get']('ergo', {}) %}
{% set service = ergo.get('service', {}) %}
{% set paths = ergo.get('paths', {}) %}
{% set network = ergo.get('network', {}) %}
{% set server = ergo.get('server', {}) %}
{% set listeners = ergo.get('listeners', {}) %}
{% set auth = ergo.get('auth', {}) %}
{% set accounts = ergo.get('accounts', {}) %}
{% set oauth2 = ergo.get('oauth2', {}) %}
{% set channels = ergo.get('channels', {}) %}
{% set motd = ergo.get('motd', {}) %}

ergo::configuration::required_pillar:
  test.check_pillar:
    - string:
      - ergo:service:user
      - ergo:service:group
      - ergo:service:shell
      - ergo:service:home
      - ergo:service:unit_file
      - ergo:paths:configuration_directory
      - ergo:paths:configuration_file
      - ergo:paths:data_directory
      - ergo:paths:tls_directory
      - ergo:paths:certificate_file
      - ergo:paths:certificate_key_file
      - ergo:paths:auth_script_file
      - ergo:paths:channel_script_file
      - ergo:paths:managed_channels_file
      - ergo:paths:motd_file
      - ergo:network:name
      - ergo:server:name
{% if not server.get('websocket_origins') %}
      - ergo:server:websocket_origin
{% endif %}{# if not server.get('websocket_origins') #}
      - ergo:server:ip_cloaking:netname
      - ergo:listeners:irc:address
      - ergo:listeners:websocket:address
      - ergo:auth:ldap_uri
      - ergo:auth:base_dn
      - ergo:auth:required_group
      - ergo:accounts:login_throttling:duration
      - ergo:oauth2:introspection_timeout
      - ergo:motd:contents
    - boolean:
      - ergo:service:system_user
      - ergo:service:create_home
      - ergo:oauth2:enabled
      - ergo:oauth2:autocreate
      - ergo:server:lookup_hostnames
      - ergo:server:forward_confirm_hostnames
      - ergo:server:ip_cloaking:enabled
      - ergo:server:ip_cloaking:enabled_for_always_on
      - ergo:accounts:login_throttling:enabled
    - integer:
      - ergo:service:gid
      - ergo:accounts:login_throttling:max_attempts
    - listing:
      - ergo:server:proxy_allowed_from
{% if server.get('websocket_origins') %}
      - ergo:server:websocket_origins
{% endif %}{# if server.get('websocket_origins') #}
      - ergo:auth:allowed_groups
      - ergo:channels:auto_join
    - failhard: true

ergo::group:
  group.present:
    - name: {{ service.group }}
    - system: true
    - gid: {{ service.gid }}
    - require:
      - test: ergo::configuration::required_pillar

ergo::user:
  user.present:
    - name: {{ service.user }}
    - system: {{ service.system_user | yaml }}
    - shell: {{ service.shell }}
    - home: {{ service.home }}
    - createhome: {{ service.create_home | yaml }}
    - gid: {{ service.group }}
    - require:
      - group: ergo::group
      - test: ergo::configuration::required_pillar

ergo::configuration_directory:
  file.directory:
    - name: {{ paths.configuration_directory }}
    - user: root
    - group: {{ service.group }}
    - mode: '0750'
    - require:
      - user: ergo::user
      - test: ergo::configuration::required_pillar

ergo::data_directory:
  file.directory:
    - name: {{ paths.data_directory }}
    - user: {{ service.user }}
    - group: {{ service.group }}
    - mode: '0750'
    - makedirs: true
    - recurse:
      - user
      - group
    - require:
      - user: ergo::user
      - test: ergo::configuration::required_pillar

ergo::tls_directory:
  file.directory:
    - name: {{ paths.tls_directory }}
    - user: root
    - group: {{ service.group }}
    - mode: '0750'
    - makedirs: true
    - require:
      - user: ergo::user
      - test: ergo::configuration::required_pillar

ergo::bootstrap_tls_certificate:
  cmd.run:
    - name: >-
        openssl req -x509 -nodes -newkey rsa:2048
        -keyout {{ paths.certificate_key_file }}
        -out {{ paths.certificate_file }}
        -days 7
        -subj /CN={{ server.name }} &&
        chown root:{{ service.group }} {{ paths.certificate_file }} {{ paths.certificate_key_file }} &&
        chmod 0640 {{ paths.certificate_file }} {{ paths.certificate_key_file }}
    - unless: test -s {{ paths.certificate_file }} -a -s {{ paths.certificate_key_file }}
    - require:
      - pkg: ergo::openssl
      - file: ergo::tls_directory
      - test: ergo::configuration::required_pillar

{{ paths.auth_script_file }}:
  file.managed:
    - source: salt://ergo/files/ergo_lldap_auth.py
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - pkg: ergo::ldap_utils
      - test: ergo::configuration::required_pillar

{{ paths.channel_script_file }}:
  file.managed:
    - source: salt://ergo/files/ergo_ensure_channel.py
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - test: ergo::configuration::required_pillar

{{ paths.managed_channels_file }}:
  file.serialize:
    - formatter: json
    - dataset: {{ channels.get('managed', []) | yaml }}
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - require:
      - file: ergo::configuration_directory
      - test: ergo::configuration::required_pillar

{{ paths.motd_file }}:
  file.managed:
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
{% if motd.get('source') %}
    - source: {{ motd.source }}
{% else %}
    - contents_pillar: ergo:motd:contents
{% endif %}
    - require:
      - file: ergo::configuration_directory
      - test: ergo::configuration::required_pillar

{{ paths.configuration_file }}:
  file.managed:
    - source: salt://ergo/templates/ircd.yaml.j2
    - template: jinja
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - context:
        paths: {{ paths | yaml }}
        network: {{ network | yaml }}
        server: {{ server | yaml }}
        listeners: {{ listeners | yaml }}
        auth: {{ auth | yaml }}
        accounts: {{ accounts | yaml }}
        oauth2: {{ oauth2 | yaml }}
        channels: {{ channels | yaml }}
    - require:
      - file: ergo::configuration_directory
      - file: ergo::data_directory
      - file: ergo::tls_directory
      - file: {{ paths.auth_script_file }}
      - file: {{ paths.channel_script_file }}
      - file: {{ paths.managed_channels_file }}
      - file: {{ paths.motd_file }}
      - cmd: ergo::bootstrap_tls_certificate
      - test: ergo::configuration::required_pillar
