{% set drop_ins = salt['pillar.get']('systemd:drop_ins', {}) %}

systemd::drop_ins::required_pillar:
  test.check_pillar:
    - dictionary:
      - systemd:drop_ins
{% for drop_in_name in drop_ins %}
      - systemd:drop_ins:{{ drop_in_name }}
      - systemd:drop_ins:{{ drop_in_name }}:configuration
{% endfor %}
{% if drop_ins %}
    - string:
{%   for drop_in_name, drop_in in drop_ins.items() %}
      - systemd:drop_ins:{{ drop_in_name }}:drop_in_directory
      - systemd:drop_ins:{{ drop_in_name }}:drop_in_file
{%     if drop_in.get('service') or drop_in.get('persistent_storage_directory') %}
      - systemd:drop_ins:{{ drop_in_name }}:service
{%     endif %}{# drop_in.service #}
{%     if drop_in.get('persistent_storage_directory') %}
      - systemd:drop_ins:{{ drop_in_name }}:persistent_storage_directory
      - systemd:drop_ins:{{ drop_in_name }}:persistent_storage_group
      - systemd:drop_ins:{{ drop_in_name }}:persistent_storage_flushed_file
{%     endif %}{# drop_in.persistent_storage_directory #}
{%   endfor %}{# drop_in_name, drop_in #}
{% endif %}
{% set daemon_reload = namespace(enabled=false) %}
{% for drop_in_name, drop_in in drop_ins.items() %}
{%   if drop_in.get('daemon_reload') is not none %}
{%     set daemon_reload.enabled = true %}
{%   endif %}{# drop_in.daemon_reload #}
{% endfor %}{# drop_in_name, drop_in #}
{% if daemon_reload.enabled %}
    - boolean:
{%   for drop_in_name, drop_in in drop_ins.items() %}
{%     if drop_in.get('daemon_reload') is not none %}
      - systemd:drop_ins:{{ drop_in_name }}:daemon_reload
{%     endif %}{# drop_in.daemon_reload #}
{%   endfor %}{# drop_in_name, drop_in #}
{% endif %}
    - failhard: true

{% for drop_in_name, drop_in in drop_ins.items() %}
{% set drop_in_directory = drop_in.get('drop_in_directory', '') %}
{% set drop_in_file = drop_in.get('drop_in_file', '') %}
{% set persistent_storage_directory = drop_in.get('persistent_storage_directory') %}
{% set persistent_storage_group = drop_in.get('persistent_storage_group') %}
{% set configuration = drop_in.get('configuration', {}) %}
systemd::drop_ins::{{ drop_in_name }}::directory:
  file.directory:
    - name: {{ drop_in_directory }}
    - user: root
    - group: root
    - mode: '0755'
    - makedirs: true
    - require:
      - test: systemd::drop_ins::required_pillar

{% if persistent_storage_directory and persistent_storage_group %}
systemd::drop_ins::{{ drop_in_name }}::persistent_storage_directory:
  file.directory:
    - name: {{ persistent_storage_directory }}
    - user: root
    - group: {{ persistent_storage_group }}
    - mode: '2755'
    - makedirs: true
    - require:
      - test: systemd::drop_ins::required_pillar

{% endif %}
{{ drop_in_file }}:
  file.managed:
    - source: salt://systemd/templates/drop_in.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        configuration: {{ configuration | yaml }}
    - require:
      - file: systemd::drop_ins::{{ drop_in_name }}::directory
      - test: systemd::drop_ins::required_pillar
{% if persistent_storage_directory and persistent_storage_group %}
      - file: systemd::drop_ins::{{ drop_in_name }}::persistent_storage_directory
{% endif %}

{%   if drop_in.get('daemon_reload') %}
systemd::drop_ins::{{ drop_in_name }}::daemon_reload:
  module.run:
    - service.systemctl_reload: []
    - onchanges:
      - file: {{ drop_in_file }}

{%   endif %}{# drop_in.daemon_reload #}
{%   if drop_in.get('service') %}
systemd::drop_ins::{{ drop_in_name }}::service:
  service.running:
    - name: {{ drop_in.service }}
    - watch:
      - file: {{ drop_in_file }}
{% if persistent_storage_directory and persistent_storage_group %}
      - file: systemd::drop_ins::{{ drop_in_name }}::persistent_storage_directory
{% endif %}

{%   endif %}{# drop_in.service #}
{% if persistent_storage_directory and persistent_storage_group %}
# A restart loads Storage/SplitMode; the flush switches this boot out of /run.
systemd::drop_ins::{{ drop_in_name }}::flush:
  cmd.run:
    - name: journalctl --flush && test -f {{ drop_in.get('persistent_storage_flushed_file', '') | yaml }}
    - creates: {{ drop_in.get('persistent_storage_flushed_file', '') | yaml }}
    - require:
      - test: systemd::drop_ins::required_pillar
      - file: {{ drop_in_file }}
      - file: systemd::drop_ins::{{ drop_in_name }}::persistent_storage_directory
      - service: systemd::drop_ins::{{ drop_in_name }}::service

{% endif %}
{% endfor %}{# drop_in_name, drop_in #}
