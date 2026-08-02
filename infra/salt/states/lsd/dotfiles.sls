{% for username, user_config in salt['pillar.get']('users', {}).items() if user_config is mapping and user_config.get('deploy', False) %}

lsd::{{ username }}::bashrc:
  file.managed:
    - name: {{ salt['userpaths.get_bashrc_dir'](username) }}/999-lsd.sh
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0644'
    - makedirs: true
    - contents: |
        alias ls='lsd'

        if [ -f /opt/packages/lsd/autocomplete/lsd.bash-completion ]; then
            . /opt/packages/lsd/autocomplete/lsd.bash-completion
            complete -F _lsd ls
        fi
    - require:
      - pkg: lsd::apt::remove

{% endfor %}{# username #}
