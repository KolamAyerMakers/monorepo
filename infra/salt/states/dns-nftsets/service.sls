include:
  - dns-nftsets.configuration
  - nftables
  - unbound

{% set dns_nftsets = salt['pillar.get']('dns-nftsets', {}) %}
{% set configuration = dns_nftsets.get('configuration', {}) %}
{% set service = dns_nftsets.get('service', {}) %}

dns-nftsets::service::required_pillar:
  test.check_pillar:
    - string:
      - dns-nftsets:configuration:path
      - dns-nftsets:service:name
      - dns-nftsets:service:script_path
      - dns-nftsets:service:unit_file
      - dns-nftsets:service:timer_file
      - dns-nftsets:service:on_boot
      - dns-nftsets:service:on_unit_active
      - dns-nftsets:service:accuracy
    - failhard: true

dns-nftsets::unit_file:
  file.managed:
    - name: {{ service.unit_file }}
    - source: salt://dns-nftsets/files/dns-nftsets.service.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        configuration_path: {{ configuration.path }}
        script_path: {{ service.script_path }}
    - require:
      - file: dns-nftsets::script
      - concat: dns-nftsets::configuration_file
      - test: dns-nftsets::service::required_pillar

dns-nftsets::timer_file:
  file.managed:
    - name: {{ service.timer_file }}
    - source: salt://dns-nftsets/files/dns-nftsets.timer.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        service_name: {{ service.name }}
        on_boot: {{ service.on_boot }}
        on_unit_active: {{ service.on_unit_active }}
        accuracy: {{ service.accuracy }}
    - require:
      - file: dns-nftsets::unit_file
      - test: dns-nftsets::service::required_pillar

dns-nftsets::daemon_reload:
  cmd.run:
    - name: systemctl daemon-reload
    - onchanges:
      - file: dns-nftsets::unit_file
      - file: dns-nftsets::timer_file

dns-nftsets::service:
  cmd.run:
    - name: systemctl start {{ service.name }}.service
    - require:
      - cmd: dns-nftsets::daemon_reload
      - file: dns-nftsets::unit_file
      - concat: dns-nftsets::configuration_file
      - cmd: nftables::reload
      - service: unbound::service
      - test: dns-nftsets::service::required_pillar
    - onchanges:
      - file: dns-nftsets::script
      - file: dns-nftsets::unit_file
      - concat: dns-nftsets::configuration_file
      - cmd: nftables::reload

dns-nftsets::timer:
  service.running:
    - name: {{ service.name }}.timer
    - enable: true
    - require:
      - cmd: dns-nftsets::daemon_reload
      - file: dns-nftsets::timer_file
      - cmd: dns-nftsets::service
    - watch:
      - file: dns-nftsets::timer_file
