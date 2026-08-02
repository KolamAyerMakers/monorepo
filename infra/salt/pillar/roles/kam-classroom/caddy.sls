{% from "roles/kam-classroom/domain_helpers.sls" import public_hostname with context %}

caddy:
  local_certs: false
  domain: {{ public_hostname }}
  docs_site_directory: /var/www/maker-guide-docs/current
  learner_routes_file: /etc/caddy/learner-routes.caddy
