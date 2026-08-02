include:
  - gamja.package

{% set gamja = salt['pillar.get']('gamja', {}) %}
{% set paths = gamja.get('paths', {}) %}
{% set server = gamja.get('server', {}) %}
{% set oauth2 = gamja.get('oauth2', {}) %}

gamja::config::required_pillar:
  test.check_pillar:
    - string:
      - gamja:paths:web_root
      - gamja:paths:configuration_file
      - gamja:server:websocket_url
      - gamja:server:auth
      - gamja:oauth2:url
      - gamja:oauth2:client_id
      - gamja:oauth2:scope
    - integer:
      - gamja:server:ping
    - boolean:
      - gamja:server:autoconnect
    - listing:
      - gamja:server:autojoin
    - failhard: true

{{ paths.configuration_file }}:
  file.managed:
    - source: salt://gamja/templates/config.json.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        server: {{ server | yaml }}
        oauth2: {{ oauth2 | yaml }}
    - require:
      - file: {{ paths.web_root }}
      - test: gamja::config::required_pillar
