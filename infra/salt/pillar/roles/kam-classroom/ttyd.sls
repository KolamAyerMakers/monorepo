{% from "roles/kam-classroom/domain_helpers.sls" import https_url, public_hostname with context %}

ttyd:
  web:
    assets:
      route: /ssh/ttyd-assets
      directory: /var/lib/ttyd/assets
      favicon:
        name: terminal.svg
        source: salt://ttyd/files/terminal.svg
      fonts:
        - name: HackNerdFontMono-Regular.ttf
          url: https://github.com/ryanoasis/nerd-fonts/raw/v3.4.0/patched-fonts/Hack/Regular/HackNerdFontMono-Regular.ttf
          checksum: sha256=03e60d3c1a9f8bef4e1f78836f80aacb9ec005260a6b094f5bfc10043bb115ab
          family: HackNerdFontMono
          weight: 400
          style: normal
          format: truetype
        - name: HackNerdFontMono-Bold.ttf
          url: https://github.com/ryanoasis/nerd-fonts/raw/v3.4.0/patched-fonts/Hack/Bold/HackNerdFontMono-Bold.ttf
          checksum: sha256=711084fdea9f9eb4e5dbca372a19e6a5af996fc88bfce55918eeef560f0f6722
          family: HackNerdFontMono
          weight: 700
          style: normal
          format: truetype
        - name: HackNerdFontMono-Italic.ttf
          url: https://github.com/ryanoasis/nerd-fonts/raw/v3.4.0/patched-fonts/Hack/Italic/HackNerdFontMono-Italic.ttf
          checksum: sha256=86c6e1b14e2cb02ac8041269c53dac3673c70ff58375d1aafe0ecff8087f8126
          family: HackNerdFontMono
          weight: 400
          style: italic
          format: truetype
        - name: HackNerdFontMono-BoldItalic.ttf
          url: https://github.com/ryanoasis/nerd-fonts/raw/v3.4.0/patched-fonts/Hack/BoldItalic/HackNerdFontMono-BoldItalic.ttf
          checksum: sha256=82fca6ff9e87bc65b6abb1bbde1e3884fa9418bfb14f15b9db2d3274b87bf44e
          family: HackNerdFontMono
          weight: 700
          style: italic
          format: truetype
    custom_index:
      path: /var/lib/ttyd/index.html
      builder: /usr/local/sbin/ttyd-build-custom-index
      stylesheet_path: /ssh/ttyd-assets/ttyd-fonts.css
      build_port: 17682
  instances:
    registration:
      server:
        domain: {{ public_hostname }}
        host: 127.0.0.1
        port: 7681
      command: /usr/bin/ssh -tt -o PreferredAuthentications=none -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR new@localhost
    ssh:
      run_user: root
      run_group: root
      auth_header: X-WEBAUTH-USER
      private_tmp: false
      protect_home: false
      read_write_paths:
        - /var/lib/ttyd
        - /home
        - /tmp
      server:
        domain: {{ public_hostname }}
        url: {{ https_url('ssh') }}
        socket: /run/ttyd-ssh/ssh.sock
        socket_owner: caddy:caddy
        upstream: unix//run/ttyd-ssh/ssh.sock
      index: /var/lib/ttyd/index.html
      client_options:
        - fontFamily=HackNerdFontMono,monospace
      command: /usr/local/sbin/ttyd-ssh-sso
