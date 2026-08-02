#!jinja|yaml|age

kam_classroom:
  bot:
    irc_account: guide
    irc_channels:
      - "#lf2607"
    docs_site:
      directory: /var/www/maker-guide-docs
      output: /var/www/maker-guide-docs/current
    sync_derived_data:
      makers_root: /makers
      documents_root: /docs
      service_file: /etc/systemd/system/maker-guide-sync-derived-data.service
      timer_file: /etc/systemd/system/maker-guide-sync-derived-data.timer
      on_boot: 1m
      on_unit_active: 1m
      accuracy: 30s
    openrouter_egress:
      nftables_file: /etc/nftables.d/47-maker-guide-openrouter-egress.nft
      header: "# Maker Guide OpenRouter egress policy"
      destination: maker-guide-openrouter
      set_v4: maker_guide_openrouter_v4
      set_v6: maker_guide_openrouter_v6
      destination_position: '27'
      domain_position: '67'
      tcp_port: 443
      domains:
        - openrouter.ai
    openrouter_api_key: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBmUDd5enNBWnRYSU1uZGk3alR5T2dlb1ExRzU0TmVqZlVNVlVzZVE1NDFzCm9CczdXSGpFOEJVMHhvQ2hvMmp4S3pQV010bHhXV21lZmZmc29jYjRuTDQKLT4gVUwnRVkzRC1ncmVhc2UKZU5KcGt2TEJsZHlDR25aSGVQSWVMVWl1dGUyMXY4SXZJSm15bHYvVWprM09Kb3hpQTluOENjam9xQkkwMnlkawprT21RUldiYndMY2JQZzY5bmQyWHhydnBDL0U4RGk5K3l4Q3FvZwotLS0gTGNwUysxZWN4SXhwMEZYd084eFo2Z0lIb2VOek41TFhEbDE0VUs5bHF6OApRTKyolLAXFsWAbxsMWXfdMgnnj+/ZGVAhs3abu/m0HVX9PIia1usssLSd+X84ntzWV3zi5FxWrGW7ghrjqPn6CMeOpdPI1EndO6QEmCL4BD1E0AUIozxhZstrBBalNs68pjUlSb6NhZzR]
