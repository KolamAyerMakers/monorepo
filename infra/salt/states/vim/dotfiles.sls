{% for username, user_config in salt['pillar.get']('users', {}).items() if user_config is mapping and user_config.get('deploy', False) %}

vim::{{ username }}::vimrc:
  file.managed:
    - name: {{ salt['userpaths.get_home'](username) }}/.vimrc
    - mode: '0644'
    - source: salt://vim/files/vimrc
    - user: {{ username }}
    - group: {{ username }}
    - require:
      - user: users::{{ username }}::user

{% endfor %}{# username #}
