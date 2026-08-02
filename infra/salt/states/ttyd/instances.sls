include:
  - ttyd.package

{% set ttyd = salt['pillar.get']('ttyd', {}) %}
{% set service = ttyd.get('service', {}) %}
{% set instances = ttyd.get('instances', {}) %}
{% set web = ttyd.get('web', {}) %}
{% set web_assets = web.get('assets', {}) %}
{% set web_fonts = web_assets.get('fonts', []) %}
{% set web_favicon = web_assets.get('favicon', {}) %}
{% set custom_index = web.get('custom_index', {}) %}
{% set web_assets_directory = web_assets.get('directory', '') %}
{% set web_assets_route = web_assets.get('route', '') %}
{% set web_favicon_path = web_assets_route ~ '/' ~ web_favicon.get('name', '') %}
{% set web_fonts_directory = web_assets_directory ~ '/fonts' %}
{% set web_fonts_stylesheet = web_assets_directory ~ '/ttyd-fonts.css' %}
{% set custom_index_command_parts = [
  custom_index.get('builder', ''),
  '--output',
  custom_index.get('path', ''),
  '--stylesheet',
  custom_index.get('stylesheet_path', ''),
  '--favicon',
  web_favicon_path,
  '--font-family',
  web_fonts[0].get('family', '') if web_fonts else '',
  '--port',
  custom_index.get('build_port', '') | string,
] %}
{% set custom_index_command = custom_index_command_parts | join(' ') %}

ttyd::instances::required_pillar:
  test.check_pillar:
    - string:
      - ttyd:service:user
      - ttyd:service:group
      - ttyd:service:shell
      - ttyd:service:home
      - ttyd:service:unit_directory
      - ttyd:service:system_call_architectures
    - boolean:
      - ttyd:service:system_user
      - ttyd:service:create_home
      - ttyd:service:protect_clock
      - ttyd:service:protect_kernel_logs
      - ttyd:service:restrict_realtime
    - integer:
      - ttyd:service:uid
      - ttyd:service:gid
    - dictionary:
      - ttyd:instances
    - failhard: true

{% if web %}
ttyd::web::required_pillar:
  test.check_pillar:
    - string:
      - ttyd:web:assets:route
      - ttyd:web:assets:directory
      - ttyd:web:assets:favicon:name
      - ttyd:web:assets:favicon:source
      - ttyd:web:custom_index:path
      - ttyd:web:custom_index:builder
      - ttyd:web:custom_index:stylesheet_path
{% for font in web_fonts %}
      - ttyd:web:assets:fonts:{{ loop.index0 }}:name
      - ttyd:web:assets:fonts:{{ loop.index0 }}:url
      - ttyd:web:assets:fonts:{{ loop.index0 }}:checksum
      - ttyd:web:assets:fonts:{{ loop.index0 }}:family
      - ttyd:web:assets:fonts:{{ loop.index0 }}:style
      - ttyd:web:assets:fonts:{{ loop.index0 }}:format
{% endfor %}{# font #}
    - integer:
      - ttyd:web:custom_index:build_port
{% for font in web_fonts %}
      - ttyd:web:assets:fonts:{{ loop.index0 }}:weight
{% endfor %}{# font #}
    - listing:
      - ttyd:web:assets:fonts
    - failhard: true

{{ web_assets_directory }}:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - makedirs: true
    - require:
      - user: ttyd::user
      - test: ttyd::web::required_pillar

{{ web_fonts_directory }}:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - file: {{ web_assets_directory }}
      - test: ttyd::web::required_pillar

ttyd::web::favicon:
  file.managed:
    - name: {{ web_assets_directory }}/{{ web_favicon.name }}
    - source: {{ web_favicon.source }}
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: {{ web_assets_directory }}
      - test: ttyd::web::required_pillar

{% for font in web_fonts %}
ttyd::web::font::{{ font.name }}:
  file.managed:
    - name: {{ web_fonts_directory }}/{{ font.name }}
    - source: {{ font.url }}
    - source_hash: {{ font.checksum }}
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: {{ web_fonts_directory }}
      - test: github::download_egress::ready
      - test: ttyd::web::required_pillar

{% endfor %}{# font #}
{{ web_fonts_stylesheet }}:
  file.managed:
    - source: salt://ttyd/templates/web-fonts.css.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        asset_route: {{ web_assets_route | tojson }}
        fonts: {{ web_fonts | yaml }}
    - require:
      - file: {{ web_assets_directory }}
{% for font in web_fonts %}
      - file: ttyd::web::font::{{ font.name }}
{% endfor %}{# font #}
      - test: ttyd::web::required_pillar

{{ custom_index.builder }}:
  file.managed:
    - source: salt://ttyd/files/ttyd_build_custom_index.py
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - test: ttyd::web::required_pillar

ttyd::web::custom_index::initial:
  cmd.run:
    - name: {{ custom_index_command }}
    - creates: {{ custom_index.path }}
    - require:
      - packages: ttyd
      - file: {{ custom_index.builder }}
      - file: ttyd::web::favicon
      - file: {{ web_fonts_stylesheet }}
      - test: ttyd::web::required_pillar

ttyd::web::custom_index::updated:
  cmd.run:
    - name: {{ custom_index_command }}
    - onchanges:
      - packages: ttyd
      - file: {{ custom_index.builder }}
      - file: ttyd::web::favicon
      - file: {{ web_fonts_stylesheet }}
    - require:
      - packages: ttyd
      - file: {{ custom_index.builder }}
      - file: ttyd::web::favicon
      - file: {{ web_fonts_stylesheet }}
      - test: ttyd::web::required_pillar

ttyd::web::custom_index::file:
  file.managed:
    - name: {{ custom_index.path }}
    - replace: false
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - cmd: ttyd::web::custom_index::initial
      - cmd: ttyd::web::custom_index::updated
      - test: ttyd::web::required_pillar

{% endif %}{# if web #}

ttyd::group:
  group.present:
    - name: {{ service.group }}
    - system: {{ service.system_user | yaml }}
    - gid: {{ service.gid }}
    - require:
      - test: ttyd::instances::required_pillar

ttyd::user:
  user.present:
    - name: {{ service.user }}
    - system: {{ service.system_user | yaml }}
    - uid: {{ service.uid }}
    - shell: {{ service.shell }}
    - home: {{ service.home }}
    - createhome: {{ service.create_home | yaml }}
    - gid: {{ service.group }}
    - require:
      - group: ttyd::group
      - test: ttyd::instances::required_pillar

ttyd::home:
  file.directory:
    - name: {{ service.home }}
    - user: {{ service.user }}
    - group: {{ service.group }}
    - mode: '0755'
    - makedirs: true
    - require:
      - user: ttyd::user
      - test: ttyd::instances::required_pillar

{% for instance_name, instance in instances.items() %}
{% set run_user = instance.get('run_user', service.user) %}
{% set run_group = instance.get('run_group', service.group) %}
{% set auth_header = instance.get('auth_header', '') %}
{% set private_tmp = instance.get('private_tmp', true) %}
{% set protect_home = instance.get('protect_home', true) %}
{% set read_write_paths = instance.get('read_write_paths', [service.home]) %}
{% set index = instance.get('index', '') %}
{% set client_options = instance.get('client_options', []) %}
ttyd::instance::{{ instance_name }}::required_pillar:
  test.check_pillar:
    - string:
      - ttyd:instances:{{ instance_name }}:command
{% if instance.get('server', {}).get('socket') %}
      - ttyd:instances:{{ instance_name }}:server:socket
      - ttyd:instances:{{ instance_name }}:server:socket_owner
{%   if instance_name == 'ssh' %}
      - ttyd:instances:{{ instance_name }}:server:domain
      - ttyd:instances:{{ instance_name }}:server:url
{%   endif %}{# if instance_name == 'ssh' #}
{% else %}
      - ttyd:instances:{{ instance_name }}:server:host
{% endif %}
{% if auth_header %}
      - ttyd:instances:{{ instance_name }}:auth_header
{% endif %}
{% if index %}
      - ttyd:instances:{{ instance_name }}:index
{% endif %}
{% if instance.get('run_user') %}
      - ttyd:instances:{{ instance_name }}:run_user
{% endif %}
{% if instance.get('run_group') %}
      - ttyd:instances:{{ instance_name }}:run_group
{% endif %}
{% if instance.get('private_tmp') is not none %}
    - boolean:
      - ttyd:instances:{{ instance_name }}:private_tmp
{% endif %}
{% if instance.get('protect_home') is not none %}
    - boolean:
      - ttyd:instances:{{ instance_name }}:protect_home
{% endif %}
{% if client_options %}
    - listing:
      - ttyd:instances:{{ instance_name }}:client_options
{% endif %}
{% if not instance.get('server', {}).get('socket') %}
    - integer:
      - ttyd:instances:{{ instance_name }}:server:port
{% endif %}
    - failhard: true

{% if instance_name == 'ssh' %}
/usr/local/sbin/ttyd-ssh-sso:
  file.managed:
    # The helper is role-specific even though ttyd owns instance units.
    - source: salt://roles/kam-classroom/templates/ttyd_ssh_sso.sh.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0755'
    - context:
        web_ssh_url: {{ instance.server.url | tojson }}
    - require:
      - test: ttyd::instance::ssh::required_pillar

{% endif %}
{{ service.unit_directory }}/ttyd-{{ instance_name }}.service:
  file.managed:
    - source: salt://ttyd/templates/ttyd-instance.service.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        service: {{ service | yaml }}
        instance_name: {{ instance_name | tojson }}
        server: {{ instance.server | yaml }}
        command: {{ instance.command | tojson }}
        run_user: {{ run_user | tojson }}
        run_group: {{ run_group | tojson }}
        auth_header: {{ auth_header | tojson }}
        private_tmp: {{ private_tmp | yaml }}
        protect_home: {{ protect_home | yaml }}
        read_write_paths: {{ read_write_paths | yaml }}
        index: {{ index | tojson }}
        client_options: {{ client_options | yaml }}
    - require:
      - test: ttyd::instances::required_pillar
      - test: ttyd::instance::{{ instance_name }}::required_pillar
{% if instance_name == 'ssh' %}
      - file: /usr/local/sbin/ttyd-ssh-sso
{% endif %}

ttyd::instance::{{ instance_name }}::systemd_daemon_reload:
  module.run:
    - service.systemctl_reload: []
    - onchanges:
      - file: {{ service.unit_directory }}/ttyd-{{ instance_name }}.service

ttyd::instance::{{ instance_name }}::service:
  service.running:
    - name: ttyd-{{ instance_name }}
    - enable: true
    - require:
      - packages: ttyd
      - file: ttyd::home
      - file: {{ service.unit_directory }}/ttyd-{{ instance_name }}.service
      - module: ttyd::instance::{{ instance_name }}::systemd_daemon_reload
      - test: ttyd::instances::required_pillar
      - test: ttyd::instance::{{ instance_name }}::required_pillar
{% if index and custom_index %}
      - cmd: ttyd::web::custom_index::initial
      - cmd: ttyd::web::custom_index::updated
      - file: ttyd::web::custom_index::file
{% endif %}
    - watch:
      - packages: ttyd
      - file: {{ service.unit_directory }}/ttyd-{{ instance_name }}.service
{% if instance_name == 'ssh' %}
      - file: /usr/local/sbin/ttyd-ssh-sso
{% endif %}
{% if index and custom_index %}
      - cmd: ttyd::web::custom_index::initial
      - cmd: ttyd::web::custom_index::updated
{% endif %}
{% endfor %}
