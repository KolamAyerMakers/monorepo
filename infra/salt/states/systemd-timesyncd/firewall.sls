include:
  - dns-nftsets.configuration
  - nftables
  - systemd-timesyncd.package

{% set configuration = salt['pillar.get']('systemd-timesyncd:config', {}) %}
{% set firewall = salt['pillar.get']('systemd-timesyncd:firewall', {}) %}
{% set dns_nftsets = salt['pillar.get']('dns-nftsets', {}) %}
{% set dns_nftsets_configuration = dns_nftsets.get('configuration', {}) %}
{% set ntp_servers = (configuration.get('ntp', []) + configuration.get('fallback_ntp', [])) | unique | list %}

systemd-timesyncd::firewall::required_pillar:
  test.check_pillar:
    - string:
      - systemd-timesyncd:firewall:destination
      - systemd-timesyncd:firewall:set_v4
      - systemd-timesyncd:firewall:set_v6
      - systemd-timesyncd:service:user
      - dns-nftsets:configuration:path
      - dns-nftsets:configuration:set_timeout
    - listing:
      - systemd-timesyncd:config:ntp
      - systemd-timesyncd:config:fallback_ntp
    - integer:
      - systemd-timesyncd:firewall:port
    - failhard: true

systemd-timesyncd::firewall::dns_nftsets:
  dns_nftsets.fragment:
    - target: {{ dns_nftsets_configuration.path }}
    - destination_position: '30'
    - domain_position: '70'
    - destinations:
        {{ firewall.destination }}:
          family: inet
          table: filter
          set_v4: {{ firewall.set_v4 }}
          set_v6: {{ firewall.set_v6 }}
    - domains:
{% for ntp_server in ntp_servers %}
      - exact: {{ ntp_server }}
        destination: {{ firewall.destination }}
{% endfor %}
    - require_in:
      - concat: dns-nftsets::configuration_file
    - require:
      - test: systemd-timesyncd::firewall::required_pillar

/etc/nftables.d/45-systemd-timesyncd.nft:
  file.managed:
    - source: salt://systemd-timesyncd/systemd-timesyncd.nft.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        firewall: {{ firewall | yaml }}
        service: {{ salt['pillar.get']('systemd-timesyncd:service', {}) | yaml }}
        set_timeout: {{ dns_nftsets_configuration.set_timeout }}
    - require:
      - file: /etc/nftables.d
      - pkg: systemd-timesyncd::package
      - test: systemd-timesyncd::firewall::required_pillar
    - watch_in:
      - cmd: nftables::validate
