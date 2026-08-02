{% set supplementary_groups = salt['pillar.get']('unbound:service:supplementary_groups', []) %}
{% set local_zone_files = salt['pillar.get']('unbound:local_zone_files', []) %}

/etc/unbound/unbound.conf:
  file.managed:
    - source: salt://unbound/templates/unbound.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - pkg: unbound

/etc/unbound/unbound.conf.d:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - clean: true
    - require:
      - pkg: unbound

{% for zone_file in local_zone_files %}
unbound::local_zone_file::{{ zone_file.identifier }}:
  file.managed:
    - name: {{ zone_file.path }}
    - user: root
    - group: root
    - mode: '0644'
    - makedirs: true
    - contents: |
        # Managed by Salt — do not edit manually
        server:
            local-zone: "{{ zone_file.zone.name }}" {{ zone_file.zone.type }}
{%   for record in zone_file.local_data_records %}            local-data: "{{ record.name }} IN {{ record.type }} {{ record.data }}"
{%   endfor -%}{# for record in zone_file.local_data_records #}
    - require_in:
      - file: /etc/unbound/unbound.conf.d
{% endfor %}{# for zone_file in local_zone_files #}

# Clean up obsolete tmpfiles.d and systemd drop-in from previous attempts
/etc/tmpfiles.d/unbound.conf:
  file.absent: []

/etc/systemd/system/unbound.service.d:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'

{% if supplementary_groups %}
{%   for group in supplementary_groups %}
unbound::supplementary_group::{{ group }}:
  group.present:
    - name: {{ group }}
    - system: true
{%   endfor %}{# for group in supplementary_groups #}

/etc/systemd/system/unbound.service.d/10-supplementary-groups.conf:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
        [Service]
        SupplementaryGroups={{ supplementary_groups | join(' ') }}
    - require:
      - file: /etc/systemd/system/unbound.service.d
{% else %}
/etc/systemd/system/unbound.service.d/10-supplementary-groups.conf:
  file.absent: []
{% endif %}{# if supplementary_groups #}

unbound::daemon_reload:
  module.run:
    - service.systemctl_reload: []
    - onchanges:
      - file: /etc/systemd/system/unbound.service.d/10-supplementary-groups.conf
