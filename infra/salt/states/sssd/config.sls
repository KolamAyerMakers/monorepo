include:
  - sssd.package

{% set sssd = salt['pillar.get']('sssd', {}) %}
{% set pam_profiles = sssd.get('pam_auth_update', {}).get('enabled_profiles', []) | join(' --enable ') %}

{% if sssd.get('enabled', false) %}
sssd::configuration::required_pillar:
  test.check_pillar:
    - string:
      - sssd:configuration_file
      - sssd:configuration_directory
      - sssd:domain_configuration_directory
      - sssd:nsswitch:passwd
      - sssd:nsswitch:group
      - sssd:nsswitch:shadow
      - sssd:nsswitch:gshadow
      - sssd:nsswitch:hosts
      - sssd:nsswitch:networks
      - sssd:nsswitch:protocols
      - sssd:nsswitch:services
      - sssd:nsswitch:ethers
      - sssd:nsswitch:rpc
      - sssd:nsswitch:netgroup
    - failhard: true

{{ sssd.configuration_directory }}:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - pkg: sssd::package
      - test: sssd::configuration::required_pillar

{{ sssd.domain_configuration_directory }}:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - file: {{ sssd.configuration_directory }}

{{ sssd.configuration_file }}:
  file.managed:
    - source: salt://sssd/templates/sssd.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0640'
    - require:
      - file: {{ sssd.configuration_directory }}
      - test: sssd::configuration::required_pillar

{% for domain_name, domain in sssd.get('domains', {}).items() %}
{{ sssd.domain_configuration_directory }}/{{ domain_name }}.conf:
  file.managed:
    - source: salt://sssd/templates/domain.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0640'
    - context:
        domain_name: {{ domain_name }}
    - require:
      - file: {{ sssd.domain_configuration_directory }}
      - test: sssd::configuration::required_pillar

{% endfor %}
sssd::configuration::nsswitch:
  file.managed:
    - name: /etc/nsswitch.conf
    - source: salt://sssd/templates/nsswitch.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - pkg: libnss-sss
      - test: sssd::configuration::required_pillar

sssd::configuration::pam_profiles:
  cmd.run:
    - name: pam-auth-update --package --enable {{ pam_profiles }}
    - unless: grep -q 'pam_sss.so' /etc/pam.d/common-auth && grep -q 'pam_mkhomedir.so' /etc/pam.d/common-session
    - require:
      - pkg: libpam-sss
{% else %}
sssd::configuration::disabled:
  test.nop:
    - comment: SSSD is disabled.
{% endif %}
