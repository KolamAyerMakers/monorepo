include:
  - dns-nftsets.package

{% set dns_nftsets = salt['pillar.get']('dns-nftsets', {}) %}
{% set configuration = dns_nftsets.get('configuration', {}) %}
{% set resolver = configuration.get('resolver', {}) %}
{% set ttl = configuration.get('ttl', {}) %}
{% set resolver_json = (
  '"resolver":{"address":"' ~ resolver.address ~ '","port":' ~ resolver.port
  ~ ',"timeout":' ~ resolver.timeout ~ ',"lifetime":' ~ resolver.lifetime ~ '}'
) %}
{% set ttl_json = (
  '"ttl":{"minimum_seconds":' ~ ttl.minimum_seconds
  ~ ',"maximum_seconds":' ~ ttl.maximum_seconds ~ '}'
) %}
{% set service = dns_nftsets.get('service', {}) %}

dns-nftsets::configuration::required_pillar:
  test.check_pillar:
    - string:
      - dns-nftsets:configuration:path
      - dns-nftsets:configuration:resolver:address
      - dns-nftsets:service:script_path
    - integer:
      - dns-nftsets:configuration:resolver:port
      - dns-nftsets:configuration:ttl:minimum_seconds
      - dns-nftsets:configuration:ttl:maximum_seconds
    - present:
      - dns-nftsets:configuration:resolver:timeout
      - dns-nftsets:configuration:resolver:lifetime
    - failhard: true

/etc/dns-nftsets:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'

/usr/local/libexec:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'

dns-nftsets::script:
  file.managed:
    - name: {{ service.script_path }}
    - source: salt://dns-nftsets/files/dns_nftsets.py
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - file: /usr/local/libexec
      - pkg: dns-nftsets::dependencies
      - test: dns-nftsets::configuration::required_pillar

dns-nftsets::configuration::settings:
  concat.fragment:
    - target: {{ configuration.path }}
    - position: '00'
    - contents: |
        # Managed by Salt.
        {"kind":"settings",{{ resolver_json }},{{ ttl_json }}}
    - require:
      - file: /etc/dns-nftsets
      - test: dns-nftsets::configuration::required_pillar
    - require_in:
      - concat: dns-nftsets::configuration_file

dns-nftsets::configuration_file:
  concat.managed:
    - name: {{ configuration.path }}
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/dns-nftsets
      - concat: dns-nftsets::configuration::settings
      - test: dns-nftsets::configuration::required_pillar
