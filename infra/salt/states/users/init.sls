{% for username, user_config in salt['pillar.get']('users', {}).items() if user_config is mapping and user_config.get('deploy', False) %}
{%   set uid = user_config.get('uid') %}
{%   set home = user_config.get('home') or salt['userpaths.get_home'](username) %}
{%   set prefix = salt['userpaths.get_local_prefix'](username) %}
{%   set local_prefix_target = user_config.get('local_prefix') %}
{%   set ssh_authorized_keys = user_config.get('ssh_authorized_keys', []) %}

users::{{ username }}::group:
  group.present:
    - name: {{ username }}
    {% if uid %}
    - gid: {{ uid }}
    {% endif %}{# uid #}

users::{{ username }}::user:
  user.present:
    - name: {{ username }}
    - home: {{ home }}
    - shell: /bin/bash
    {% if uid %}
    - uid: {{ uid }}
    - gid: {{ uid }}
    {% endif %}{# uid #}
    - require:
      - group: users::{{ username }}::group

users::{{ username }}::home:
  file.directory:
    - name: {{ home }}
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0700'
    - require:
      - user: users::{{ username }}::user

{%   if ssh_authorized_keys %}
users::{{ username }}::ssh_authorized_keys:
  ssh_auth.present:
    - user: {{ username }}
    - names: {{ ssh_authorized_keys | yaml }}
    - require:
      - user: users::{{ username }}::user

{%   endif %}{# ssh_authorized_keys #}

users::{{ username }}::config_dir:
  file.directory:
    - name: {{ salt['userpaths.get_config_dir'](username) }}
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0755'
    - require:
      - user: users::{{ username }}::user

{%   if local_prefix_target %}
users::{{ username }}::local_prefix::symlink:
  file.symlink:
    - name: {{ prefix }}
    - target: {{ local_prefix_target }}
    - force: true
    - require:
      - user: users::{{ username }}::user
{%   endif %}{# local_prefix_target #}

users::{{ username }}::local_prefix::directory:
  file.directory:
    - name: {{ prefix }}
    - user: {{ username }}
    - group: {{ username }}
    - mode: "0755"
    - makedirs: true
    {% if local_prefix_target %}
    - skip_verify: true
    {% endif %}{# local_prefix_target #}
    - require:
      - user: users::{{ username }}::user

users::{{ username }}::local_prefix::subdirs:
  file.directory:
    - names:
      - {{ prefix }}/bin
      - {{ prefix }}/state
      - {{ prefix }}/share
      - {{ prefix }}/share/man
      - {{ prefix }}/share/man/man1
      - {{ prefix }}/packages
    - user: {{ username }}
    - group: {{ username }}
    - mode: "0755"
    - require:
      - user: users::{{ username }}::user

{% endfor %}{# username #}
