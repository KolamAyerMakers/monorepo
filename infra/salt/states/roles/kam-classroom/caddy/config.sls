include:
  - roles.kam-classroom.caddy.package
  - forgejo.service
  - lldap.service
  - authelia.service
  - gamja.config
  - ttyd.instances

{% set forgejo = salt['pillar.get']('forgejo', {}) %}
{% set forgejo_server = forgejo.get('server', {}) %}
{% set lldap = salt['pillar.get']('lldap', {}) %}
{% set lldap_http = lldap.get('http', {}) %}
{% set authelia = salt['pillar.get']('authelia', {}) %}
{% set authelia_server = authelia.get('server', {}) %}
{% set gamja = salt['pillar.get']('gamja', {}) %}
{% set gamja_paths = gamja.get('paths', {}) %}
{% set ergo = salt['pillar.get']('ergo', {}) %}
{% set ergo_server = ergo.get('server', {}) %}
{% set ergo_listeners = ergo.get('listeners', {}) %}
{% set ttyd = salt['pillar.get']('ttyd', {}) %}
{% set ttyd_instances = ttyd.get('instances', {}) %}
{% set ttyd_web = ttyd.get('web', {}) %}
{% set ttyd_web_assets = ttyd_web.get('assets', {}) %}
{% set registration_ttyd = ttyd_instances.get('registration', {}) %}
{% set registration_ttyd_server = registration_ttyd.get('server', {}) %}
{% set ssh_ttyd = ttyd_instances.get('ssh', {}) %}
{% set ssh_ttyd_server = ssh_ttyd.get('server', {}) %}
{% set caddy = salt['pillar.get']('caddy', {}) %}

kam-classroom::caddy::configuration::required_pillar:
  test.check_pillar:
    - string:
      - forgejo:server:domain
      - forgejo:server:http_address
      - lldap:http:domain
      - lldap:http:host
      - lldap:http:url
      - authelia:server:domain
      - authelia:server:host
      - authelia:server:url
      - gamja:paths:web_root
      - ergo:server:name
      - ergo:listeners:websocket:address
      - ttyd:instances:registration:server:domain
      - ttyd:instances:registration:server:host
      - ttyd:instances:ssh:server:domain
      - ttyd:instances:ssh:server:upstream
      - ttyd:web:assets:route
      - ttyd:web:assets:directory
      - caddy:configuration_directory
      - caddy:configuration_file
      - caddy:docs_site_directory
      - caddy:domain
      - caddy:learner_routes_file
    - boolean:
      - caddy:local_certs
    - integer:
      - forgejo:server:http_port
      - lldap:http:port
      - authelia:server:port
      - ttyd:instances:registration:server:port
    - failhard: true

{{ caddy.configuration_directory }}:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - pkg: kam-classroom::caddy::package
      - test: kam-classroom::caddy::configuration::required_pillar

{{ caddy.configuration_file }}:
  file.managed:
    - source: salt://roles/kam-classroom/caddy/templates/Caddyfile.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        forgejo_server: {{ forgejo_server | yaml }}
        lldap_http: {{ lldap_http | yaml }}
        authelia_server: {{ authelia_server | yaml }}
        gamja_paths: {{ gamja_paths | yaml }}
        ergo_server: {{ ergo_server | yaml }}
        ergo_listeners: {{ ergo_listeners | yaml }}
        registration_ttyd_server: {{ registration_ttyd_server | yaml }}
        ssh_ttyd_server: {{ ssh_ttyd_server | yaml }}
        ttyd_web_assets: {{ ttyd_web_assets | yaml }}
        caddy: {{ caddy | yaml }}
    - require:
      - file: {{ caddy.configuration_directory }}
      - service: forgejo::service
      - service: lldap::service
      - service: authelia::service
      - service: ttyd::instance::registration::service
      - service: ttyd::instance::ssh::service
      - file: {{ ttyd_web_assets.directory }}
      - file: {{ gamja_paths.web_root }}
      - test: kam-classroom::caddy::configuration::required_pillar

{{ caddy.learner_routes_file }}:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: ''
    - replace: false
    - require:
      - file: {{ caddy.configuration_directory }}
      - test: kam-classroom::caddy::configuration::required_pillar

/usr/local/sbin/refresh-learner-routes:
  file.managed:
    - source: salt://roles/kam-classroom/caddy/templates/refresh-learner-routes.sh.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0750'
    - context:
        database_path: /var/lib/maker-guide/state.db
        domain: {{ caddy.domain | tojson }}
        configuration_file: {{ caddy.configuration_file | tojson }}
        learner_routes_file: {{ caddy.learner_routes_file | tojson }}
    - require:
      - file: {{ caddy.configuration_file }}
      - file: {{ caddy.learner_routes_file }}

kam-classroom::caddy::configuration::validate:
  cmd.run:
    - name: caddy validate --config {{ caddy.configuration_file }}
    - onchanges:
      - file: {{ caddy.configuration_file }}
    - require:
      - pkg: kam-classroom::caddy::package
      - file: {{ caddy.configuration_file }}
      - test: kam-classroom::caddy::configuration::required_pillar
