{% for username, user_config in salt['pillar.get']('users', {}).items() if user_config is mapping and user_config.get('deploy', False) %}
{%   set home = salt['userpaths.get_home'](username) %}
{%   set bashrc_d = salt['userpaths.get_bashrc_dir'](username) %}

bash::{{ username }}::bash_profile:
  file.managed:
    - name: {{ home }}/.bash_profile
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0644'
    - source: salt://bash/files/bash_profile
    - require:
      - user: users::{{ username }}::user

bash::{{ username }}::bashrc:
  file.managed:
    - name: {{ home }}/.bashrc
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0644'
    - source: salt://bash/files/bashrc
    - require:
      - user: users::{{ username }}::user

bash::{{ username }}::bashrc.d:
  file.directory:
    - name: {{ bashrc_d }}
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0755'
    - source: salt://bash/files/bashrc.d
    - require:
      - user: users::{{ username }}::user

{%   for path in salt['cp.list_master'](prefix='bash/files/bashrc.d/') %}
{%     set filename = path.split('/')[-1] %}
bash::{{ username }}::bashrc.d/{{ filename }}:
  file.managed:
    - name: {{ bashrc_d }}/{{ filename }}
    - source: salt://{{ path }}
    - mode: '0644'
    - user: {{ username }}
    - group: {{ username }}
    - require:
      - user: users::{{ username }}::user
{%   endfor %}{# bash/files/bashrc.d/ #}

{%   for path in salt['cp.list_master'](prefix='bash/templates/bashrc.d/') %}
{%     set filename = path.split('/')[-1][:-3] %}
bash::{{ username }}::bashrc.d/{{ filename }}:
  file.managed:
    - name: {{ bashrc_d }}/{{ filename }}
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0644'
    - source: salt://{{ path }}
    - template: jinja
    - require:
      - user: users::{{ username }}::user
{%   endfor %}{# bash/templates/bashrc.d/ #}

{% endfor %}{# username #}
