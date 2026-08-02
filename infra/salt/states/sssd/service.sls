include:
  - sssd.config

{% set sssd = salt['pillar.get']('sssd', {}) %}

{% if sssd.get('enabled', false) %}
sssd::service:
  service.running:
    - name: sssd
    - enable: true
    - require:
      - pkg: sssd::package
      - pkg: sssd-tools
      - pkg: libnss-sss
      - pkg: libpam-sss
      - pkg: libsss-sudo
      - file: {{ sssd.configuration_file }}
      - file: sssd::configuration::nsswitch
      - cmd: sssd::configuration::pam_profiles
    - watch:
      - file: {{ sssd.configuration_file }}
      - file: sssd::configuration::nsswitch
{% for domain_name in sssd.get('domains', {}) %}
      - file: {{ sssd.domain_configuration_directory }}/{{ domain_name }}.conf
{% endfor %}
{% else %}
sssd::service::disabled:
  test.nop:
    - comment: SSSD is disabled.
{% endif %}
