{% for username, user_config in salt['pillar.get']('users', {}).items() if user_config is mapping and user_config.get('deploy', False) %}

starship::{{ username }}::config:
  file.managed:
    - name: {{ salt['userpaths.get_config_dir'](username) }}/starship.toml
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0644'
    - source: salt://starship/files/starship.toml
    - require:
      - user: users::{{ username }}::user

starship::{{ username }}::default_profile:
  file.managed:
    - name: {{ salt['userpaths.get_config_dir'](username) }}/starship-default.toml
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0644'
    - source: salt://starship/files/starship.toml
    - require:
      - user: users::{{ username }}::user

starship::{{ username }}::minimal_profile:
  file.managed:
    - name: {{ salt['userpaths.get_config_dir'](username) }}/starship-minimal.toml
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0644'
    - source: salt://starship/files/starship-minimal.toml
    - require:
      - user: users::{{ username }}::user

starship::{{ username }}::classic_profile:
  file.managed:
    - name: {{ salt['userpaths.get_config_dir'](username) }}/starship-classic.toml
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0644'
    - source: salt://starship/files/starship-classic.toml
    - require:
      - user: users::{{ username }}::user

starship::{{ username }}::bashrc:
  file.managed:
    - name: {{ salt['userpaths.get_bashrc_dir'](username) }}/999-starship.sh
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0644'
    - source: salt://starship/templates/bashrc.sh.j2
    - template: jinja
    - require:
      - file: bash::{{ username }}::bashrc.d

{% endfor %}{# username #}
