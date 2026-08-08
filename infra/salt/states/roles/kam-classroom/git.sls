{% set default_branch = salt['pillar.get']('kam_classroom:git:default_branch') %}

roles::kam_classroom::git::required_pillar:
  test.check_pillar:
    - string:
      - kam_classroom:git:default_branch
    - failhard: true

roles::kam_classroom::git::default_branch:
  cmd.run:
    - name: /usr/bin/git config --system init.defaultBranch {{ default_branch|yaml }}
    - unless: /usr/bin/test "$(/usr/bin/git config --system --get init.defaultBranch)" = {{ default_branch|yaml }}
    - require:
      - test: roles::kam_classroom::git::required_pillar
