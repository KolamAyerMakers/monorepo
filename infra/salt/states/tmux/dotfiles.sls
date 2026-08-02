tmux::root::config:
  file.managed:
    - name: /root/.tmux.conf
    - source: salt://tmux/templates/tmux.conf.j2
    - template: jinja
    - context:
        tpm_enabled: false
    - user: root
    - group: root
    - mode: '0644'

{% for username, user_config in salt['pillar.get']('users', {}).items() if user_config is mapping and user_config.get('deploy', False) %}
{%   set home = salt['userpaths.get_home'](username) %}
tmux::{{ username }}::config:
  file.managed:
    - name: {{ home }}/.tmux.conf
    - source: salt://tmux/templates/tmux.conf.j2
    - template: jinja
    - context:
        tpm_enabled: true
    - user: {{ username }}
    - group: {{ username }}
{% endfor %}{# username #}
