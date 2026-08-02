kam_classroom:
  npm_egress:
    nftables_file: /etc/nftables.d/48-classroom-npm-egress.nft
    header: "# Classroom npm registry egress policy"
    destination: classroom-npm
    set_v4: classroom_npm_v4
    set_v6: classroom_npm_v6
    destination_position: '28'
    domain_position: '68'
    # LLDAP's humans group.
    gid: 1001
    user: maker-guide
    tcp_port: 443
    domains:
      - registry.npmjs.org
