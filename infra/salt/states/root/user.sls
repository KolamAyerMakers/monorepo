root::user:
  user.present:
    - name: root
    - fullname: root
    - shell: /bin/bash
    - home: /root
    - uid: 0
    - gid: 0
    - password: "{{ salt['pillar.get']('root:password', '!') }}"
