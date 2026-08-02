packages:
  lldap:
    version: 0.6.3
    arch:
      x86_64:
        libc: static
        url: https://github.com/lldap/lldap/releases/download/v{version}/amd64-lldap.tar.gz
        checksum: sha256=e80b50ef39be61de9f1d75182b1e1fa5d82c672261c7e34fd8ffec5455ed3883
      aarch64:
        libc: static
        url: https://github.com/lldap/lldap/releases/download/v{version}/aarch64-lldap.tar.gz
        checksum: sha256=3843e3fde8dff0d2a16c51f62ec2ed318916e722857d20daa61d9175a2b7c020
    scope: system
    strip_components: 1
    binaries:
      lldap: lldap
      lldap_set_password: lldap_set_password
      lldap_migration_tool: lldap_migration_tool
