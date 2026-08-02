include:
  - roles.kam-classroom.identity
  - dns-nftsets.configuration
  - dns-nftsets.service
  - nftables

{% set bot = salt['pillar.get']('kam_classroom:bot', {}) %}
{% set identity = salt['pillar.get']('kam_classroom:identity', {}) %}
{% set registration_user = identity.get('registration_user', {}).get('user', '') %}
{% set ergo = salt['pillar.get']('ergo', {}) %}
{% set commands = (
  'maker-guide-bot',
  'maker-guide-bash-hook',
  'maker-guide-build-docs',
  'maker-guide-build-personal-website',
  'maker-guide-calendar',
  'maker-guide-check-doc-links',
  'maker-guide-create-learner',
  'maker-guide-db',
  'maker-guide-export-audit',
  'guide',
  'maker-guide-help',
  'maker-guide-initialize-learner',
  'maker-guide-grant-group',
  'maker-guide-prune-llm-audit',
  'maker-guide-prune-observations',
  'maker-guide-ops',
  'maker-guide-progress',
  'maker-guide-register',
  'maker-guide-registration',
  'maker-guide-render-learner-routes',
  'maker-guide-revoke-group',
  'maker-guide-sync-derived-data',
  'maker-guide-sync-groups',
) %}
{% set daemon_user = bot.get('user', 'maker-guide') %}
{% set daemon_group = bot.get('group', 'maker-guide') %}
{% set database_group = bot.get('database_group', 'mentors') %}
{% set irc_account = bot.get('irc_account', '') %}
{% set runtime_group = bot.get('runtime_group', identity.get('default_group', 'humans')) %}
{% set config_path = bot.get('config_path', '/etc/maker-guide/config.toml') %}
{% set database_path = bot.get('database_path', '/var/lib/maker-guide/state.db') %}
{% set socket_path = bot.get('socket_path', '/run/maker-guide/preexec.sock') %}
{% set sync_derived_data = bot.get('sync_derived_data', {}) %}
{% set docs_site = bot.get('docs_site', {}) %}
{% set docs_site_directory = docs_site.get('directory', '') %}
{% set docs_site_output = docs_site.get('output', '') %}
{% set makers_root = sync_derived_data.get('makers_root', '') %}
{% set documents_root = sync_derived_data.get('documents_root', '') %}
{% set irc_channels = bot.get('irc_channels', []) %}
{% set irc_server = ergo.get('server', {}).get('name', '') %}
{% set irc_password_file = bot.get('irc_password_file', '/etc/maker-guide/secrets/irc-password') %}
{% set maker_guide_executable = '/usr/local/lib/maker-guide/current' %}
{% set openrouter_api_key = bot.get('openrouter_api_key', '') %}
{% set openrouter_api_key_file = '/etc/maker-guide/secrets/openrouter-api-key' %}
{% set openrouter_egress = bot.get('openrouter_egress', {}) %}
{% set dns_nftsets_configuration = salt['pillar.get']('dns-nftsets', {}).get('configuration', {}) %}
{% set openrouter_counter = 'output_maker_guide_openrouter' %}
{% set openrouter_comment = 'maker-guide openrouter' %}

roles::kam_classroom::bot::required_pillar:
  test.check_pillar:
    - string:
      - dns-nftsets:configuration:path
      - dns-nftsets:configuration:set_timeout
      - ergo:server:name
      - kam_classroom:bot:irc_account
      - kam_classroom:bot:openrouter_api_key
      - kam_classroom:bot:openrouter_egress:nftables_file
      - kam_classroom:bot:openrouter_egress:header
      - kam_classroom:bot:openrouter_egress:destination
      - kam_classroom:bot:openrouter_egress:set_v4
      - kam_classroom:bot:openrouter_egress:set_v6
      - kam_classroom:bot:openrouter_egress:destination_position
      - kam_classroom:bot:openrouter_egress:domain_position
      - kam_classroom:bot:docs_site:directory
      - kam_classroom:bot:docs_site:output
      - kam_classroom:bot:sync_derived_data:makers_root
      - kam_classroom:bot:sync_derived_data:documents_root
      - kam_classroom:bot:sync_derived_data:service_file
      - kam_classroom:bot:sync_derived_data:timer_file
      - kam_classroom:bot:sync_derived_data:on_boot
      - kam_classroom:bot:sync_derived_data:on_unit_active
      - kam_classroom:bot:sync_derived_data:accuracy
    - integer:
      - kam_classroom:bot:openrouter_egress:tcp_port
    - listing:
      - kam_classroom:bot:irc_channels
      - kam_classroom:bot:openrouter_egress:domains
    - failhard: true

roles::kam_classroom::bot::group:
  group.present:
    - name: {{ daemon_group }}
    - system: true

roles::kam_classroom::bot::user:
  user.present:
    - name: {{ daemon_user }}
    - gid: {{ daemon_group }}
    - home: /var/lib/maker-guide
    - shell: /usr/sbin/nologin
    - createhome: false
    - system: true
    - require:
      - group: roles::kam_classroom::bot::group

roles::kam_classroom::bot::openrouter_dns_nftsets:
  dns_nftsets.fragment:
    - target: {{ dns_nftsets_configuration.path }}
    - destination_position: {{ openrouter_egress.destination_position }}
    - domain_position: {{ openrouter_egress.domain_position }}
    - destinations:
        {{ openrouter_egress.destination }}:
          family: inet
          table: filter
          set_v4: {{ openrouter_egress.set_v4 }}
          set_v6: {{ openrouter_egress.set_v6 }}
    - domains:
{% for domain in openrouter_egress.get('domains', []) %}
      - exact: {{ domain }}
        destination: {{ openrouter_egress.destination }}
{% endfor %}{# for domain in openrouter_egress.get('domains', []) #}
    - require_in:
      - concat: dns-nftsets::configuration_file
    - require:
      - test: roles::kam_classroom::bot::required_pillar

roles::kam_classroom::bot::openrouter_egress:
  nftables_file.managed:
    - name: {{ openrouter_egress.nftables_file }}
    - header: "{{ openrouter_egress.header }}"
    - counters:
      - {{ openrouter_counter }}
    - sets:
      - name: {{ openrouter_egress.set_v4 }}
        type: ipv4_addr
        flags:
          - timeout
        timeout: {{ dns_nftsets_configuration.set_timeout }}
        position: '25'
      - name: {{ openrouter_egress.set_v6 }}
        type: ipv6_addr
        flags:
          - timeout
        timeout: {{ dns_nftsets_configuration.set_timeout }}
        position: '25'
    - chains:
      - name: output
        position: '60'
    - rules:
      - chain: output
        position: '10'
        rule: >-
          meta skuid {{ daemon_user }} ip daddr @{{ openrouter_egress.set_v4 }}
          tcp dport {{ openrouter_egress.tcp_port }} counter name "{{ openrouter_counter }}"
          accept comment "{{ openrouter_comment }}"
      - chain: output
        position: '11'
        rule: >-
          meta skuid {{ daemon_user }} ip6 daddr @{{ openrouter_egress.set_v6 }}
          tcp dport {{ openrouter_egress.tcp_port }} counter name "{{ openrouter_counter }}"
          accept comment "{{ openrouter_comment }}"
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/nftables.d
      - test: roles::kam_classroom::bot::required_pillar
      - user: roles::kam_classroom::bot::user
    - require_in:
      - cmd: dns-nftsets::service
    - onchanges_in:
      - cmd: nftables::reload
    - watch_in:
      - cmd: nftables::validate

roles::kam_classroom::bot::configuration_directory:
  file.directory:
    - name: /etc/maker-guide
    - user: root
    - group: {{ daemon_group }}
    - mode: '0755'
    - makedirs: true
    - require:
      - user: roles::kam_classroom::bot::user

roles::kam_classroom::bot::secrets_directory:
  file.directory:
    - name: /etc/maker-guide/secrets
    - user: root
    - group: {{ daemon_group }}
    - mode: '0750'
    - makedirs: true
    - require:
      - file: roles::kam_classroom::bot::configuration_directory

roles::kam_classroom::bot::irc_password_generated:
  cmd.run:
    - name: |
        /usr/bin/python3 <<'PYTHON'
        from pathlib import Path
        import secrets

        Path({{ irc_password_file | tojson }}).write_text(
            secrets.token_urlsafe(48) + "\n",
            encoding="utf-8",
        )
        PYTHON
    - unless: test -s {{ irc_password_file }}
    - require:
      - file: roles::kam_classroom::bot::secrets_directory

{{ irc_password_file }}:
  file.managed:
    - user: root
    - group: {{ daemon_group }}
    - mode: '0640'
    - replace: false
    - require:
      - cmd: roles::kam_classroom::bot::irc_password_generated

{{ openrouter_api_key_file }}:
  file.managed:
    - user: root
    - group: {{ daemon_group }}
    - mode: '0640'
    - contents: |
        {{ openrouter_api_key | trim }}
    - require:
      - file: roles::kam_classroom::bot::secrets_directory

roles::kam_classroom::bot::guide_password:
  cmd.run:
    - name: /usr/local/sbin/lldap-set-password {{ irc_account }} --password-stdin < {{ irc_password_file }}
    - unless: /usr/local/sbin/lldap-set-password {{ irc_account }} --password-stdin --check < {{ irc_password_file }}
    - require:
      - file: /usr/local/sbin/lldap-set-password
      - file: {{ irc_password_file }}
      - cmd: roles::kam_classroom::lldap_user::{{ irc_account }}

roles::kam_classroom::bot::data_directory:
  file.directory:
    - name: /var/lib/maker-guide
    - user: {{ daemon_user }}
    - group: {{ database_group }}
    - mode: '0750'
    - makedirs: true
    - require:
      - cmd: roles::kam_classroom::lldap_group::{{ database_group }}
      - user: roles::kam_classroom::bot::user
      - service: sssd::service

{{ makers_root }}:
  file.directory:
    - user: {{ daemon_user }}
    - group: {{ runtime_group }}
    - mode: '0755'
    - makedirs: true
    - require:
      - user: roles::kam_classroom::bot::user
      - service: sssd::service

{{ documents_root }}:
  file.directory:
    - user: {{ daemon_user }}
    - group: {{ runtime_group }}
    - mode: '0755'
    - makedirs: true
    - require:
      - user: roles::kam_classroom::bot::user
      - service: sssd::service

{{ docs_site_directory }}:
  file.directory:
    - user: {{ daemon_user }}
    - group: {{ runtime_group }}
    - mode: '0755'
    - makedirs: true
    - require:
      - user: roles::kam_classroom::bot::user
      - service: sssd::service

{{ docs_site_output }}:
  file.directory:
    - user: {{ daemon_user }}
    - group: {{ runtime_group }}
    - mode: '0755'
    - makedirs: true
    - require:
      - file: {{ docs_site_directory }}

{{ database_path }}:
  file.managed:
    - user: {{ daemon_user }}
    - group: {{ database_group }}
    - mode: '0640'
    - replace: false
    - require:
      - cmd: roles::kam_classroom::lldap_group::{{ database_group }}
      - file: roles::kam_classroom::bot::data_directory

{{ config_path }}:
  file.managed:
    - source: salt://roles/kam-classroom/templates/maker-guide-config.toml.j2
    - template: jinja
    - user: root
    - group: {{ daemon_group }}
    - mode: '0644'
    - context:
        socket_path: {{ socket_path | tojson }}
        runtime_group: {{ runtime_group | tojson }}
        database_path: {{ database_path | tojson }}
        irc_server: {{ irc_server | tojson }}
        irc_channels: {{ irc_channels | yaml }}
        irc_password_file: {{ irc_password_file | tojson }}
        irc_account: {{ irc_account | tojson }}
        llm_tutor_enabled: true
    - require:
      - file: roles::kam_classroom::bot::configuration_directory
      - file: roles::kam_classroom::bot::data_directory
      - file: {{ irc_password_file }}
      - file: {{ openrouter_api_key_file }}

roles::kam_classroom::bot::executable_directory:
  file.directory:
    - name: /usr/local/lib/maker-guide
    - user: root
    - group: root
    - mode: '0755'
    - makedirs: true

roles::kam_classroom::bot::release_directory:
  file.directory:
    - name: /usr/local/lib/maker-guide/releases
    - user: root
    - group: root
    - mode: '0755'
    - makedirs: true
    - require:
      - file: roles::kam_classroom::bot::executable_directory

roles::kam_classroom::bot::incoming_release:
  file.recurse:
    - name: /usr/local/lib/maker-guide/incoming
    - source: salt://roles/kam-classroom/files/maker-guide
    - clean: true
    - user: root
    - group: root
    - file_mode: '0644'
    - dir_mode: '0755'
    - require:
      - file: roles::kam_classroom::bot::executable_directory
      - test: roles::kam_classroom::bot::required_pillar

/usr/local/sbin/maker-guide-release:
  file.managed:
    - source: salt://roles/kam-classroom/files/maker-guide-release
    - user: root
    - group: root
    - mode: '0755'

roles::kam_classroom::bot::stage_release:
  cmd.run:
    - name: /usr/local/sbin/maker-guide-release /usr/local/lib/maker-guide/incoming /usr/local/lib/maker-guide/releases stage
    - unless: /usr/local/sbin/maker-guide-release /usr/local/lib/maker-guide/incoming /usr/local/lib/maker-guide/releases staged
    - require:
      - file: roles::kam_classroom::bot::incoming_release
      - file: roles::kam_classroom::bot::release_directory
      - file: /usr/local/sbin/maker-guide-release

roles::kam_classroom::bot::stop_for_release:
  cmd.run:
    - name: /usr/local/sbin/maker-guide-release /usr/local/lib/maker-guide/incoming /usr/local/lib/maker-guide/releases stop {{ registration_user | tojson }}
    - unless: /usr/local/sbin/maker-guide-release /usr/local/lib/maker-guide/incoming /usr/local/lib/maker-guide/releases active
    - require:
      - cmd: roles::kam_classroom::bot::stage_release
      - user: roles::kam_classroom::registration_user

roles::kam_classroom::bot::publish_release:
  cmd.run:
    - name: /usr/local/sbin/maker-guide-release /usr/local/lib/maker-guide/incoming /usr/local/lib/maker-guide/releases activate
    - unless: /usr/local/sbin/maker-guide-release /usr/local/lib/maker-guide/incoming /usr/local/lib/maker-guide/releases active
    - require:
      - cmd: roles::kam_classroom::bot::stop_for_release

roles::kam_classroom::bot::release_pending:
  cmd.run:
    - name: /usr/bin/true
    - onlyif: /usr/local/sbin/maker-guide-release /usr/local/lib/maker-guide/incoming /usr/local/lib/maker-guide/releases pending
    - require:
      - cmd: roles::kam_classroom::bot::publish_release

{% for command in commands %}
/usr/local/bin/{{ command }}:
  file.symlink:
    - target: {{ maker_guide_executable }}/bin/{{ command }}
    - force: true
    - require:
      - cmd: roles::kam_classroom::bot::publish_release
{% endfor %}

roles::kam_classroom::bot::build_docs:
  cmd.run:
    - name: systemctl start maker-guide-build-docs.service
    - onchanges:
      - cmd: roles::kam_classroom::bot::publish_release
      - cmd: roles::kam_classroom::bot::release_pending
    - require:
      - cmd: roles::kam_classroom::bot::database_migrate
      - module: roles::kam_classroom::bot::systemd_reload
      - cmd: roles::kam_classroom::bot::publish_release
      - file: /etc/systemd/system/maker-guide-build-docs.service

/etc/profile.d/maker-guide-bash-hook.sh:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
        case "$-" in
          *i*) ;;
          *) return 0 ;;
        esac

        if [ -z "${BASH_VERSION:-}" ]; then
          return 0
        fi

        __maker_guide_hook_enabled=0
        for __maker_guide_group in $(id -nG 2>/dev/null); do
          case "$__maker_guide_group" in
            linux-foundations)
              __maker_guide_hook_enabled=1
              break
              ;;
          esac
        done

        if [ "$__maker_guide_hook_enabled" = 1 ] && command -v maker-guide-bash-hook >/dev/null 2>&1; then
          eval "$(maker-guide-bash-hook init bash 2>/dev/null)" || true
        fi

        if [ "$__maker_guide_hook_enabled" = 1 ] && command -v maker-guide-build-personal-website >/dev/null 2>&1; then
          alias build-website='maker-guide-build-personal-website'
        fi

        unset __maker_guide_group __maker_guide_hook_enabled
    - require:
      - file: /usr/local/bin/maker-guide-bash-hook
      - file: /usr/local/bin/maker-guide-build-personal-website
      - file: /usr/local/bin/guide

roles::kam_classroom::bot::database_migrate:
  cmd.run:
    - name: /usr/local/bin/maker-guide-db --config {{ config_path }} upgrade head
    - runas: {{ daemon_user }}
    - unless: /usr/local/bin/maker-guide-db --config {{ config_path }} current --check-heads
    - require:
      - cmd: roles::kam_classroom::bot::publish_release
      - file: /usr/local/bin/maker-guide-db
      - file: {{ config_path }}
      - file: {{ database_path }}

{% for username, user in identity.get('managed_users', {}).items() %}
{%   set secondary_group_names = user.get('secondary_groups', []) %}
{%   if user.primary_group == 'linux-foundations' or 'linux-foundations' in secondary_group_names %}
{%     set rank_eligibility_option = '' if user.primary_group == 'students' or 'students' in secondary_group_names else ' --not-rank-eligible' %}
roles::kam_classroom::bot::initialize_participant::{{ username }}:
  cmd.run:
    - name: >-
        /usr/local/bin/maker-guide-initialize-learner {{ username | tojson }} --uid {{ user.uid_number }} --enroll{{ rank_eligibility_option }}
        --config {{ config_path | tojson }}
    - runas: {{ daemon_user }}
    - unless: >-
        /usr/bin/python3 -c 'import sqlite3,sys;sys.exit(sqlite3.connect(sys.argv[1]).execute(
        "select 1 from learners where handle = ?",(sys.argv[2],)).fetchone() is None)'
        {{ database_path | tojson }} {{ username | tojson }}
    - require:
      - cmd: roles::kam_classroom::bot::database_migrate
      - cmd: roles::kam_classroom::lldap_user::{{ username }}
      - file: /usr/local/bin/maker-guide-initialize-learner
      - file: {{ config_path }}
      - file: {{ database_path }}
{%   endif %}
{% endfor %}

roles::kam_classroom::bot::refresh_learner_routes:
  cmd.run:
    - name: /usr/local/sbin/refresh-learner-routes
    - onchanges:
      - cmd: roles::kam_classroom::bot::publish_release
      - cmd: roles::kam_classroom::bot::release_pending
{% for username, user in identity.get('managed_users', {}).items() %}
{%   set secondary_group_names = user.get('secondary_groups', []) %}
{%   if user.primary_group == 'linux-foundations' or 'linux-foundations' in secondary_group_names %}
      - cmd: roles::kam_classroom::bot::initialize_participant::{{ username }}
{%   endif %}
{% endfor %}
    - require:
      - cmd: roles::kam_classroom::bot::database_migrate
      - file: /usr/local/bin/maker-guide-render-learner-routes
      - file: /usr/local/sbin/refresh-learner-routes

/etc/tmpfiles.d/maker-guide.conf:
  file.managed:
    - user: root
    - group: root
    - mode: "0644"
    - contents: |
        d /run/maker-guide 2750 {{ daemon_user }} {{ runtime_group }} -
    - require:
      - user: roles::kam_classroom::bot::user

roles::kam_classroom::bot::create_directories:
  file.directory:
    - name: /run/maker-guide
    - user: {{ daemon_user }}
    - group: {{ runtime_group }}
    - mode: '2750'
    - require:
      - file: /etc/tmpfiles.d/maker-guide.conf
      - user: roles::kam_classroom::bot::user
      - service: sssd::service

/etc/systemd/system/maker-guide-bot.service:
  file.managed:
    - source: salt://roles/kam-classroom/templates/maker-guide-bot.service.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        daemon_user: {{ daemon_user | tojson }}
        daemon_group: {{ daemon_group | tojson }}
        runtime_group: {{ runtime_group | tojson }}
        config_path: {{ config_path | tojson }}
    - require:
      - cmd: roles::kam_classroom::bot::publish_release
      - file: /usr/local/bin/maker-guide-bot
      - file: {{ config_path }}

{{ sync_derived_data.service_file }}:
  file.managed:
    - source: salt://roles/kam-classroom/templates/maker-guide-sync-derived-data.service.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        daemon_user: {{ daemon_user | tojson }}
        daemon_group: {{ daemon_group | tojson }}
        runtime_group: {{ runtime_group | tojson }}
        config_path: {{ config_path | tojson }}
        makers_root: {{ makers_root | tojson }}
        documents_root: {{ documents_root | tojson }}
    - require:
      - cmd: roles::kam_classroom::bot::publish_release
      - file: /usr/local/bin/maker-guide-sync-derived-data
      - file: {{ config_path }}
      - file: {{ makers_root }}
      - file: {{ documents_root }}

{{ sync_derived_data.timer_file }}:
  file.managed:
    - source: salt://roles/kam-classroom/templates/maker-guide-sync-derived-data.timer.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        on_boot: {{ sync_derived_data.on_boot | tojson }}
        on_unit_active: {{ sync_derived_data.on_unit_active | tojson }}
        accuracy: {{ sync_derived_data.accuracy | tojson }}
    - require:
      - file: {{ sync_derived_data.service_file }}

/etc/systemd/system/maker-guide-build-docs.service:
  file.managed:
    - source: salt://roles/kam-classroom/templates/maker-guide-build-docs.service.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        daemon_user: {{ daemon_user | tojson }}
        daemon_group: {{ daemon_group | tojson }}
        runtime_group: {{ runtime_group | tojson }}
        config_path: {{ config_path | tojson }}
        makers_root: {{ makers_root | tojson }}
        docs_site_directory: {{ docs_site_directory | tojson }}
        docs_site_output: {{ docs_site_output | tojson }}
    - require:
      - cmd: roles::kam_classroom::bot::publish_release
      - file: /usr/local/bin/maker-guide-build-docs
      - file: {{ config_path }}
      - file: {{ makers_root }}
      - file: {{ docs_site_directory }}
      - file: {{ docs_site_output }}

/etc/systemd/system/maker-guide-build-docs.timer:
  file.managed:
    - source: salt://roles/kam-classroom/templates/maker-guide-build-docs.timer
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /etc/systemd/system/maker-guide-build-docs.service

roles::kam_classroom::bot::systemd_reload:
  module.run:
    - service.systemctl_reload: []
    - onchanges:
      - file: /etc/systemd/system/maker-guide-bot.service
      - file: {{ sync_derived_data.service_file }}
      - file: {{ sync_derived_data.timer_file }}
      - file: /etc/systemd/system/maker-guide-build-docs.service
      - file: /etc/systemd/system/maker-guide-build-docs.timer

roles::kam_classroom::bot::sync_derived_data:
  cmd.run:
    - name: systemctl start maker-guide-sync-derived-data.service
    - onchanges:
      - file: {{ makers_root }}
      - file: {{ documents_root }}
      - cmd: roles::kam_classroom::bot::publish_release
      - cmd: roles::kam_classroom::bot::release_pending
      - file: {{ config_path }}
      - file: {{ sync_derived_data.service_file }}
    - require:
      - cmd: roles::kam_classroom::bot::database_migrate
      - module: roles::kam_classroom::bot::systemd_reload
      - file: {{ makers_root }}
      - file: {{ documents_root }}
      - file: {{ sync_derived_data.service_file }}

maker-guide-sync-derived-data.timer:
  service.running:
    - enable: true
    - require:
      - file: {{ sync_derived_data.service_file }}
      - file: {{ sync_derived_data.timer_file }}
      - cmd: roles::kam_classroom::bot::sync_derived_data
      - module: roles::kam_classroom::bot::systemd_reload

maker-guide-build-docs.timer:
  service.running:
    - enable: true
    - require:
      - cmd: roles::kam_classroom::bot::database_migrate
      - file: /etc/systemd/system/maker-guide-build-docs.service
      - file: /etc/systemd/system/maker-guide-build-docs.timer
      - module: roles::kam_classroom::bot::systemd_reload

maker-guide-bot.service:
  service.running:
    - enable: true
    - watch:
      - file: /etc/systemd/system/maker-guide-bot.service
      - file: {{ config_path }}
      - file: {{ irc_password_file }}
      - file: {{ openrouter_api_key_file }}
      - cmd: roles::kam_classroom::bot::publish_release
    - require:
      - cmd: roles::kam_classroom::bot::database_migrate
      - file: roles::kam_classroom::bot::create_directories
      - cmd: dns-nftsets::service
      - dns_nftsets: roles::kam_classroom::bot::openrouter_dns_nftsets
      - nftables_file: roles::kam_classroom::bot::openrouter_egress
      - module: roles::kam_classroom::bot::systemd_reload

roles::kam_classroom::bot::verify_active_release:
  cmd.run:
    - name: systemctl is-active --quiet maker-guide-bot.service
    - onchanges:
      - cmd: roles::kam_classroom::bot::publish_release
      - cmd: roles::kam_classroom::bot::release_pending
      - service: maker-guide-bot.service
    - require:
      - service: maker-guide-bot.service

roles::kam_classroom::bot::restore_registration:
  cmd.run:
    - name: /usr/local/sbin/maker-guide-release /usr/local/lib/maker-guide/incoming /usr/local/lib/maker-guide/releases restore-registration
    - onlyif: test -e /usr/local/lib/maker-guide/registration-open.before-release
    - require:
      - cmd: roles::kam_classroom::bot::database_migrate
      - cmd: roles::kam_classroom::bot::verify_active_release
      - cmd: roles::kam_classroom::bot::prune_releases
      - service: maker-guide-bot.service

roles::kam_classroom::bot::prune_releases:
  cmd.run:
    - name: /usr/local/sbin/maker-guide-release /usr/local/lib/maker-guide/incoming /usr/local/lib/maker-guide/releases prune
    - onchanges:
      - cmd: roles::kam_classroom::bot::verify_active_release
    - require:
      - cmd: roles::kam_classroom::bot::verify_active_release
      - cmd: roles::kam_classroom::bot::build_docs
      - cmd: roles::kam_classroom::bot::refresh_learner_routes
      - cmd: roles::kam_classroom::bot::sync_derived_data
      - file: /usr/local/sbin/maker-guide-release

roles::kam_classroom::bot::complete_release:
  cmd.run:
    - name: /usr/local/sbin/maker-guide-release /usr/local/lib/maker-guide/incoming /usr/local/lib/maker-guide/releases complete
    - onchanges:
      - cmd: roles::kam_classroom::bot::prune_releases
    - require:
      - cmd: roles::kam_classroom::bot::prune_releases
      - cmd: roles::kam_classroom::bot::restore_registration
