caddy:
  package: caddy
  service_user: caddy
  configuration_directory: /etc/caddy
  configuration_file: /etc/caddy/Caddyfile
  admin_address: unix//run/caddy/admin.sock
  runtime_directory: caddy
  runtime_directory_mode: '0700'
  service_umask: '0077'
  http_port: 80
  https_port: 443
