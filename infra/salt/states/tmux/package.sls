{% from "bootstrap/macros/packages.sls" import bootstrap_binary_package, bootstrap_package_installed %}

include:
  - github.download_egress

{{ bootstrap_package_installed('tmux') }}

{% for username, user_config in salt['pillar.get']('users', {}).items() if user_config is mapping and user_config.get('deploy', False) %}

{{ bootstrap_binary_package(
    'tmux:tpm',
    state_identifier='tmux:tpm::' ~ username,
    parameters=[
      {'scope': 'user'},
      {'user': username},
      {'binaries': false},
      {'strip_components': 1},
      {'package_dir': '{home}/.tmux/plugins/tpm'},
      {'onlyif': ['id -u ' ~ username ~ ' 2>/dev/null']},
    ],
    extra_requirements=[{'user': 'users::' ~ username ~ '::user'}]
) }}

{% endfor %}{# username #}
