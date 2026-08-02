{% for username, user_config in salt['pillar.get']('users', {}).items() if user_config is mapping and user_config.get('deploy', False) %}
{%   set home_dir = salt['userpaths.get_home'](username) %}
{%   set ssh_dir = home_dir + '/.ssh' %}
{%   set ssh_user_config = user_config.get('ssh', {}) %}
{%   set enable_session_multiplexing = ssh_user_config.get('enable_session_multiplexing') %}

ssh::{{ username }}::directory:
  file.directory:
    - name: {{ ssh_dir }}
    - mode: '0700'
    - user: {{ username }}
    - group: {{ username }}
    - require:
      - user: users::{{ username }}::user

{%   if enable_session_multiplexing %}
ssh::{{ username }}::directory::controlmasters:
  file.directory:
    - name: {{ ssh_dir }}/controlmasters
    - mode: '0700'
    - user: {{ username }}
    - group: {{ username }}
    - require:
      - file: ssh::{{ username }}::directory
{%   endif %}

ssh::{{ username }}::config:
  file.managed:
    - name: {{ ssh_dir }}/config
    - mode: '0644'
    - user: {{ username }}
    - group: {{ username }}
    - source: salt://ssh/templates/config.j2
    - template: jinja
    - context:
        enable_session_multiplexing: {{ enable_session_multiplexing | yaml }}
        config: {{ ssh_user_config.get('config', {}) | yaml }}
    - require:
      - user: users::{{ username }}::user
      - file: ssh::{{ username }}::directory

{%   set ssh_agent_sh = home_dir + '/.bashrc.d/ssh-agent.sh' %}
{%   if ssh_user_config.get('manage_ssh_agent') %}
ssh::{{ username }}::bashrc.d/ssh-agent.sh:
  file.managed:
    - name: {{ ssh_agent_sh }}
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0644'
    - source: salt://ssh/files/ssh-agent.sh
    - require:
      - user: users::{{ username }}::user
      - file: bash::{{ username }}::bashrc_d

{%   else %}
ssh::{{ username }}::bashrc.d/ssh-agent.sh:
  file.absent:
    - name: {{ ssh_agent_sh }}
{%   endif %}

{% endfor %}{# username #}
