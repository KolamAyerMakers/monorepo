{% for username, user_config in salt['pillar.get']('users', {}).items() if user_config is mapping and user_config.get('deploy', False) %}
{%   set home = salt['userpaths.get_home'](username) %}
{%   set nvim_dir = home ~ '/.config/nvim' %}

neovim::{{ username }}::config_dir:
  file.directory:
    - name: {{ nvim_dir }}
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0755'
    - require:
      - user: users::{{ username }}::user

{%   for path in salt['cp.list_master'](prefix='neovim/files/lua/') %}
{%     set target_rel = path.replace('neovim/files/lua/', '') %}
neovim::{{ username }}::lua/{{ target_rel }}:
  file.managed:
    - name: {{ nvim_dir }}/lua/{{ target_rel }}
    - source: salt://{{ path }}
    - mode: '0644'
    - user: {{ username }}
    - group: {{ username }}
    - makedirs: true
    - require:
      - file: neovim::{{ username }}::config_dir
{%   endfor %}{# lua files #}

neovim::{{ username }}::init.lua:
  file.managed:
    - name: {{ nvim_dir }}/init.lua
    - source: salt://neovim/files/init.lua
    - mode: '0644'
    - user: {{ username }}
    - group: {{ username }}
    - makedirs: true
    - require:
      - file: neovim::{{ username }}::config_dir

{% endfor %}{# username #}
