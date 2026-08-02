github:
  download_egress:
    enabled: true
    nftables_file: /etc/nftables.d/44-github-download-egress.nft
    header: "# GitHub download egress policy"
    destination: github-download
    set_v4: github_download_v4
    set_v6: github_download_v6
    destination_position: '25'
    domain_position: '65'
    user: root
    tcp_port: 443
    domains:
      # Release and source downloads can redirect between these hosts.
      - github.com
      - release-assets.githubusercontent.com
      - raw.githubusercontent.com
      - codeload.github.com
      - codeberg.org
      - code.forgejo.org
      - nodejs.org
      - registry.npmjs.org
