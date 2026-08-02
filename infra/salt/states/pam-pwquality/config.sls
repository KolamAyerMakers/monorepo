include:
  - pam-pwquality.package

{% set pam_pwquality = salt['pillar.get']('pam_pwquality', {}) %}
{% set configuration_directory = pam_pwquality.get('configuration_directory', '') %}
{% set configuration_file = pam_pwquality.get('configuration_file', '') %}
{% set cracklib_dictionary_path = pam_pwquality.get('cracklib_dictionary_path', '') %}
{% set cracklib_update_command = pam_pwquality.get('cracklib_update_command', '') %}
{% set pam_profile_command = pam_pwquality.get('pam_profile_command', '') %}
{% set pam_profile_check_command = pam_pwquality.get('pam_profile_check_command', '') %}
{% set options = pam_pwquality.get('options', {}) %}
{% set flags = pam_pwquality.get('flags', []) %}

pam-pwquality::configuration::required_pillar:
  test.check_pillar:
    - string:
      - pam_pwquality:configuration_directory
      - pam_pwquality:configuration_file
      - pam_pwquality:cracklib_dictionary_path
      - pam_pwquality:cracklib_update_command
      - pam_pwquality:pam_profile_command
      - pam_pwquality:pam_profile_check_command
    - dictionary:
      - pam_pwquality:options
    - listing:
      - pam_pwquality:flags
      - pam_pwquality:packages
    - failhard: true

{{ configuration_directory }}:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - pkg: pam-pwquality::packages
      - test: pam-pwquality::configuration::required_pillar

{{ configuration_file }}:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
{% for key, value in options.items() %}
        {{ key }} = {{ value }}
{% endfor %}
{% for flag in flags %}
        {{ flag }}
{% endfor %}
    - require:
      - file: {{ configuration_directory }}
      - pkg: pam-pwquality::packages
      - test: pam-pwquality::configuration::required_pillar

pam-pwquality::cracklib_dictionary:
  cmd.run:
    - name: {{ cracklib_update_command }}
    - creates: {{ cracklib_dictionary_path }}
    - require:
      - pkg: pam-pwquality::packages
      - test: pam-pwquality::configuration::required_pillar

pam-pwquality::pam_profile:
  cmd.run:
    - name: {{ pam_profile_command }}
    - unless: {{ pam_profile_check_command }}
    - require:
      - cmd: pam-pwquality::cracklib_dictionary
      - file: {{ configuration_file }}
      - pkg: pam-pwquality::packages
      - test: pam-pwquality::configuration::required_pillar
