{%- from "bootstrap/macros/packages.sls" import bootstrap_package_installed -%}

include:
  - quotas
  - lldap
  - forgejo.service
  - pam-pwquality.package
  - sssd

{% set identity = salt['pillar.get']('kam_classroom:identity', {}) -%}
{% set registration_user = identity.get('registration_user', {}) -%}
{% set registration_administrator = identity.get('registration_administrator') -%}
{% set registration_administrator_commands = (
  '/usr/local/bin/maker-guide-registration open, '
  ~ '/usr/local/bin/maker-guide-registration close, '
  ~ '/usr/local/bin/maker-guide-registration status'
) -%}
{% set registration_create_learner_command = (
  '/usr/local/bin/maker-guide-create-learner '
  ~ '^--registration-mode [^ /]+ --email [^ ]+ --password-stdin$'
) -%}
{% set default_group_name = identity.get('default_group') -%}
{% set managed_groups = identity.get('groups', {}) -%}
{% set managed_users = identity.get('managed_users', {}) -%}

roles::kam_classroom::identity::required_pillar:
  test.check_pillar:
    - string:
      - kam_classroom:identity:registration_user:user
      - kam_classroom:identity:registration_user:group
      - kam_classroom:identity:registration_administrator
      - kam_classroom:identity:default_group
{% for username, user in managed_users.items() %}
      - kam_classroom:identity:managed_users:{{ username }}:display_name
      - kam_classroom:identity:managed_users:{{ username }}:email
      - kam_classroom:identity:managed_users:{{ username }}:home_directory
      - kam_classroom:identity:managed_users:{{ username }}:shell
      - kam_classroom:identity:managed_users:{{ username }}:primary_group
{% endfor %}
    - dictionary:
      - kam_classroom:identity:registration_user
      - kam_classroom:identity:groups
      - kam_classroom:identity:managed_users
{% for group_name in managed_groups %}
      - kam_classroom:identity:groups:{{ group_name }}
{% endfor %}
{% for username in managed_users %}
      - kam_classroom:identity:managed_users:{{ username }}
{% endfor %}
    - integer:
      - kam_classroom:identity:registration_user:uid
      - kam_classroom:identity:registration_user:gid
{% for username in managed_users %}
      - kam_classroom:identity:managed_users:{{ username }}:uid_number
{% endfor %}
{% if managed_groups %}
{%   for group_name in managed_groups %}
      - kam_classroom:identity:groups:{{ group_name }}:gid_number
{%   endfor %}
{% endif %}
{% for username in managed_users %}
    - listing:
      - kam_classroom:identity:managed_users:{{ username }}:secondary_groups
{%   if 'ssh_public_keys' in managed_users[username] %}
      - kam_classroom:identity:managed_users:{{ username }}:ssh_public_keys
{%   endif %}
{% endfor %}
    - failhard: true

{% if default_group_name not in managed_groups %}
roles::kam_classroom::identity::default_group_is_managed:
  test.fail_without_changes:
    - name: kam_classroom:identity:default_group must reference kam_classroom:identity:groups
    - failhard: true
    - require:
      - test: roles::kam_classroom::identity::required_pillar
{% endif %}

{% for username, user in managed_users.items() %}
{%   if user.primary_group not in managed_groups %}
roles::kam_classroom::identity::managed_user::{{ username }}::primary_group_is_managed:
  test.fail_without_changes:
    - name: kam_classroom:identity:managed_users:{{ username }}:primary_group must reference kam_classroom:identity:groups
    - failhard: true
    - require:
      - test: roles::kam_classroom::identity::required_pillar
{%   endif %}
{%   for group_name in user.get('secondary_groups', []) %}
{%     if group_name not in managed_groups %}
roles::kam_classroom::identity::managed_user::{{ username }}::secondary_group::{{ group_name }}::is_managed:
  test.fail_without_changes:
    - name: kam_classroom:identity:managed_users:{{ username }}:secondary_groups must reference kam_classroom:identity:groups
    - failhard: true
    - require:
      - test: roles::kam_classroom::identity::required_pillar
{%     endif %}
{%   endfor %}
{% endfor %}

{{ bootstrap_package_installed('diceware', state_identifier='roles::kam_classroom::diceware') }}

{{ bootstrap_package_installed('sudo', state_identifier='roles::kam_classroom::sudo') }}

roles::kam_classroom::registration_group:
  group.present:
    - name: {{ registration_user.group }}
    - system: true
    - gid: {{ registration_user.gid }}

roles::kam_classroom::registration_home:
  file.directory:
    - name: /var/empty/kam-registration
    - user: root
    - group: root
    - mode: '0555'
    - makedirs: true

roles::kam_classroom::registration_user:
  user.present:
    - name: {{ registration_user.user }}
    - uid: {{ registration_user.uid }}
    - gid: {{ registration_user.group }}
    - home: /var/empty/kam-registration
    - shell: /bin/sh
    - createhome: false
    - password: ''
    - enforce_password: true
    - password_lock: false
    - system: true
    - require:
      - group: roles::kam_classroom::registration_group
      - file: roles::kam_classroom::registration_home

roles::kam_classroom::registration_user::password:
  cmd.run:
    - name: "/usr/sbin/usermod --password '' {{ registration_user.user }}"
    - unless: "/usr/bin/getent shadow {{ registration_user.user }} | /usr/bin/cut -d: -f2 | /usr/bin/grep -Fx ''"
    - require:
      - user: roles::kam_classroom::registration_user
      - test: roles::kam_classroom::identity::required_pillar

/etc/sudoers.d/kam-registration:
  file.managed:
    - user: root
    - group: root
    - mode: '0440'
    - check_cmd: /usr/sbin/visudo -c -f
    - contents: |
        {{ registration_administrator }} ALL=(root) NOPASSWD: {{ registration_administrator_commands }}
        {{ registration_user.user }} ALL=(root) NOPASSWD: /usr/local/bin/maker-guide-registration check
        {{ registration_user.user }} ALL=(root) NOPASSWD: {{ registration_create_learner_command }}
        %mentors ALL=(maker-guide) NOPASSWD: /usr/local/bin/maker-guide-progress ^release S(0[1-9]|[1-9][0-9]*) --source mentor$
        maker-guide ALL=(root) NOPASSWD: /usr/bin/systemctl start maker-guide-build-docs.service
        %mentors ALL=(root) NOPASSWD: {{ registration_administrator_commands }}
    - require:
      - pkg: roles::kam_classroom::sudo
      - cmd: roles::kam_classroom::registration_user::password

/usr/local/sbin/lldap-ensure-group:
  file.managed:
    - source: salt://roles/kam-classroom/files/lldap_ensure_group.py
    - user: root
    - group: root
    - mode: '0750'
    - require:
      - file: lldap::secret_environment_file
      - service: lldap::service
      - test: roles::kam_classroom::identity::required_pillar

/usr/local/sbin/lldap-ensure-user:
  file.managed:
    - source: salt://roles/kam-classroom/files/lldap_ensure_user.py
    - user: root
    - group: root
    - mode: '0750'
    - require:
      - file: lldap::secret_environment_file
      - service: lldap::service
      - test: roles::kam_classroom::identity::required_pillar

/usr/local/sbin/lldap_ensure_user.py:
  file.managed:
    - source: salt://roles/kam-classroom/files/lldap_ensure_user.py
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - file: /usr/local/sbin/lldap-ensure-user

/usr/local/sbin/lldap-migrate-group-members:
  file.managed:
    - source: salt://roles/kam-classroom/files/lldap_migrate_group_members.py
    - user: root
    - group: root
    - mode: '0750'
    - require:
      - file: /usr/local/sbin/lldap-ensure-user
      - file: /usr/local/sbin/lldap_ensure_user.py

{% for group_name, group in managed_groups.items() %}
roles::kam_classroom::lldap_group::{{ group_name }}:
  cmd.run:
    - name: /usr/local/sbin/lldap-ensure-group {{ group_name }} --gid-number {{ group.gid_number }}
    - unless: /usr/local/sbin/lldap-ensure-group {{ group_name }} --gid-number {{ group.gid_number }} --check
    - require:
      - file: /usr/local/sbin/lldap-ensure-group
      - test: roles::kam_classroom::identity::required_pillar
{% endfor %}

roles::kam_classroom::lldap_group_migration::lf2607:
  cmd.run:
    - name: /usr/local/sbin/lldap-migrate-group-members lf2607 linux-foundations
    - unless: /usr/local/sbin/lldap-migrate-group-members lf2607 linux-foundations --check
    - require:
      - file: /usr/local/sbin/lldap-migrate-group-members
      - cmd: roles::kam_classroom::lldap_group::lf2607
      - cmd: roles::kam_classroom::lldap_group::linux-foundations

{% for username, user in managed_users.items() %}
{%   set secondary_group_names = user.get('secondary_groups', []) %}
{%   set managed_user_command = namespace(value='/usr/local/sbin/lldap-ensure-user ' ~ (username | tojson)) %}
{%   set managed_user_command.value = managed_user_command.value ~ ' --uid-number ' ~ user.uid_number %}
{%   set managed_user_command.value = managed_user_command.value ~ ' --display-name ' ~ (user.display_name | tojson) %}
{%   set managed_user_command.value = managed_user_command.value ~ ' --email ' ~ (user.email | tojson) %}
{%   set managed_user_command.value = managed_user_command.value ~ ' --home-directory ' ~ (user.home_directory | tojson) %}
{%   set managed_user_command.value = managed_user_command.value ~ ' --shell ' ~ (user.shell | tojson) %}
{%   set managed_user_command.value = managed_user_command.value ~ ' --primary-group ' ~ (user.primary_group | tojson) %}
{%   for group_name in secondary_group_names %}
{%     set managed_user_command.value = managed_user_command.value ~ ' --secondary-group ' ~ (group_name | tojson) %}
{%   endfor %}
{%   for ssh_public_key in user.get('ssh_public_keys', []) %}
{%     set managed_user_command.value = managed_user_command.value ~ ' --ssh-public-key ' ~ (ssh_public_key | tojson) %}
{%   endfor %}
roles::kam_classroom::lldap_user::{{ username }}:
  cmd.run:
    - name: {{ managed_user_command.value | tojson }}
    - unless: {{ (managed_user_command.value ~ ' --check') | tojson }}
    - require:
      - file: /usr/local/sbin/lldap-ensure-user
      - test: roles::kam_classroom::identity::required_pillar
      - cmd: roles::kam_classroom::lldap_group::{{ user.primary_group }}
{%   for group_name in user.get('secondary_groups', []) %}
      - cmd: roles::kam_classroom::lldap_group::{{ group_name }}
{%   endfor %}
{% endfor %}

/usr/local/sbin/lldap-create-user:
  file.managed:
    - source: salt://roles/kam-classroom/files/lldap_create_user.py
    - user: root
    - group: root
    - mode: '0750'
    - require:
      - pkg: roles::kam_classroom::diceware
      - pkg: pam-pwquality::packages
      - cmd: roles::kam_classroom::lldap_group::{{ default_group_name }}
      - file: lldap::secret_environment_file
      - service: lldap::service
      - service: forgejo::service
      - file: /usr/local/sbin/apply-user-quotas

/usr/local/sbin/lldap-set-password:
  file.managed:
    - source: salt://roles/kam-classroom/files/lldap_set_password.py
    - user: root
    - group: root
    - mode: '0750'
    - require:
      - pkg: roles::kam_classroom::diceware
      - pkg: pam-pwquality::packages
      - file: lldap::secret_environment_file
      - service: lldap::service

/usr/local/sbin/lldap-delete-user:
  file.managed:
    - source: salt://roles/kam-classroom/files/lldap_delete_user.py
    - user: root
    - group: root
    - mode: '0750'
    - require:
      - file: lldap::secret_environment_file
      - service: lldap::service

/usr/local/sbin/kam-classroom-reset:
  file.managed:
    - source: salt://roles/kam-classroom/files/kam_classroom_reset.py
    - user: root
    - group: root
    - mode: '0750'
    - require:
      - file: /usr/local/sbin/lldap-delete-user
      - service: forgejo::service
      - service: lldap::service

roles::kam_classroom::sssd_uses_local_lldap:
  test.nop:
    - require:
      - service: lldap::service
      - file: /usr/local/sbin/lldap-create-user
      - file: /usr/local/sbin/lldap-set-password
      - file: /usr/local/sbin/lldap-delete-user
      - file: /usr/local/sbin/lldap-ensure-user
    - require_in:
      - service: sssd::service
