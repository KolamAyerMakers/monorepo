{% from "roles/kam-classroom/domain_helpers.sls" import public_domain, public_hostname with context %}

kam_classroom:
  domain:
    public_domain: {{ public_domain }}
    public_hostname: {{ public_hostname }}
