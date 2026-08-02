root::ssh_authorized_keys:
  ssh_auth.present:
    - user: root
    - names: {{ salt['pillar.get']('root:ssh_authorized_keys', []) | yaml }}
