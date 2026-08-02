{% set manage_resolv_conf = salt['pillar.get']('unbound:manage_resolv_conf', false) %}
{% set supplementary_groups = salt['pillar.get']('unbound:service:supplementary_groups', []) %}
{% set local_zone_files = salt['pillar.get']('unbound:local_zone_files', []) %}

{% if manage_resolv_conf %}
include:
  - systemd-resolved.disable
{% endif %}{# if manage_resolv_conf #}

unbound::service:
  service.running:
    - name: unbound
    - enable: true
    - require:
      - pkg: dns-root-data
      - pkg: unbound
      - module: unbound::daemon_reload
{% for group in supplementary_groups %}
      - group: unbound::supplementary_group::{{ group }}
{% endfor %}{# for group in supplementary_groups #}
    - watch:
      - file: /etc/unbound/unbound.conf
      - file: /etc/unbound/unbound.conf.d
{% for zone_file in local_zone_files %}
      - file: unbound::local_zone_file::{{ zone_file.identifier }}
{% endfor %}{# for zone_file in local_zone_files #}
{% if supplementary_groups %}
      - file: /etc/systemd/system/unbound.service.d/10-supplementary-groups.conf
{% endif %}{# if supplementary_groups #}

{% if manage_resolv_conf %}
unbound::mask_resolvconf_helper:
  service.masked:
    - name: unbound-resolvconf
    - require:
      - service: unbound::service
      - service: systemd-resolved::disable

unbound::reset_failed_resolvconf_helper:
  cmd.run:
    - name: systemctl reset-failed unbound-resolvconf.service
    - onlyif: systemctl is-failed --quiet unbound-resolvconf.service
    - require:
      - service: unbound::mask_resolvconf_helper

unbound::remove_resolv_conf_symlink:
  file.absent:
    - name: /etc/resolv.conf
    - onlyif: test -L /etc/resolv.conf
    - require:
      - service: unbound::service
      - service: systemd-resolved::disable
      - service: unbound::mask_resolvconf_helper
      - cmd: unbound::reset_failed_resolvconf_helper

unbound::resolv_conf:
  cmd.script:
    - name: salt://unbound/files/manage-resolv-conf.sh
    - unless: |
        test ! -L /etc/resolv.conf &&
        test -f /etc/resolv.conf &&
        grep -Fxq '# Managed by Salt — DNS handled by local Unbound' /etc/resolv.conf &&
        grep -Fxq 'nameserver 127.0.0.1' /etc/resolv.conf
    - require:
      - file: unbound::remove_resolv_conf_symlink
      - service: unbound::service
{% endif %}{# if manage_resolv_conf #}
