{% for username, user_config in salt['pillar.get']('users', {}).items() if user_config is mapping and user_config.get('deploy', False) %}

inputrc::{{ username }}::inputrc:
  file.managed:
    - name: {{ salt['userpaths.get_home'](username) }}/.inputrc
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0644'
    - source: salt://inputrc/files/inputrc

{% endfor %}{# username #}
