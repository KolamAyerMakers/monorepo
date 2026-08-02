gamja:
  version: 1.0.0-beta.11
  source:
    url: https://codeberg.org/emersion/gamja/archive/19e3ec40886a37ba46a122698e5ddb94d15f37ca.tar.gz
    checksum: sha256=6c252f91f155d3bd67967fe45172c714e5905ff8f25c2bc82cc0048f5ef92be0
  paths:
    package_directory: /opt/gamja
    web_root: /var/www/gamja
    configuration_file: /var/www/gamja/config.json
  server:
    websocket_url: wss://localhost/webirc
    autojoin: []
    auth: oauth2
    autoconnect: true
    ping: 60
  oauth2:
    url: http://localhost:9091
    client_id: gamja
    scope: openid profile groups
