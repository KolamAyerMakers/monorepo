{% from "roles/kam-classroom/domain_helpers.sls" import ldap_base_distinguished_name, public_domain with context %}

sssd:
  enabled: true
  domains:
    {{ public_domain }}:
      options:
        id_provider: ldap
        auth_provider: ldap
        chpass_provider: ldap
        access_provider: permit
        enumerate: false
        cache_credentials: true
        ldap_uri: ldap://127.0.0.1:3890/
        ldap_id_use_start_tls: false
        ldap_auth_disable_tls_never_use_in_production: true
        ldap_schema: rfc2307bis
        ldap_search_base: {{ ldap_base_distinguished_name }}
        ldap_default_bind_dn: uid=admin,ou=people,{{ ldap_base_distinguished_name }}
        ldap_user_search_base: ou=people,{{ ldap_base_distinguished_name }}?subtree?(uidNumber=*)
        ldap_user_object_class: posixAccount
        ldap_user_name: uid
        ldap_user_gecos: cn
        ldap_user_uid_number: uidNumber
        ldap_user_gid_number: gidNumber
        ldap_user_home_directory: homeDirectory
        ldap_user_shell: unixShell
        ldap_user_ssh_public_key: sshPublicKey
        ldap_group_search_base: ou=groups,{{ ldap_base_distinguished_name }}?subtree?(gidNumber=*)
        ldap_group_object_class: groupOfUniqueNames
        ldap_group_name: cn
        ldap_group_gid_number: gidNumber
        ldap_group_member: uniqueMember
      secret_options:
        ldap_default_authtok: lldap:secrets:ldap_user_pass
