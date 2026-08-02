include:
  - dns-nftsets.configuration
  - nftables

{% set apt = salt['pillar.get']('apt', {}) %}
{% set dns_nftsets = salt['pillar.get']('dns-nftsets', {}) %}
{% set configuration = dns_nftsets.get('configuration', {}) %}
{% set repository_egress = salt['apt.build_repository_egress'](apt) %}

{% if repository_egress.get('repositories') %}
apt::firewall::required_pillar:
  test.check_pillar:
    - string:
      - dns-nftsets:configuration:path
      - dns-nftsets:configuration:set_timeout
    - failhard: true

apt::firewall::dns_nftsets:
  dns_nftsets.fragment:
    - target: {{ configuration.path }}
    - destination_position: '20'
    - domain_position: '60'
    - destinations: {{ repository_egress.destinations | yaml }}
    - domains: {{ repository_egress.domains | yaml }}
    - require_in:
      - concat: dns-nftsets::configuration_file
    - require:
      - test: apt::firewall::required_pillar

/etc/nftables.d/45-apt-egress.nft:
  file.managed:
    - source: salt://apt/apt-egress.nft.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        repositories: {{ repository_egress.repositories | yaml }}
        set_timeout: {{ configuration.set_timeout }}
    - require:
      - file: /etc/nftables.d
      - test: apt::firewall::required_pillar
    - watch_in:
      - cmd: nftables::validate
{% else %}
apt::firewall::no_repositories:
  test.nop:
    - name: apt::firewall::no_repositories
{% endif %}
