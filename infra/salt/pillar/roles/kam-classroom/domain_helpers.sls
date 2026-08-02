{% set canonical_domain = 'kolamayermakers.org' %}
{% set public_domain = 'dev.' ~ canonical_domain if grains.deployment_environment == 'development' else canonical_domain %}
{% set canonical_hostname = 'lf2607.' ~ canonical_domain %}
{% set public_hostname = 'lf-dev.' ~ canonical_domain if grains.deployment_environment == 'development' else canonical_hostname %}
{% set ldap_base_distinguished_name = 'dc=' ~ (public_domain.split('.') | join(',dc=')) %}

{% macro https_url(service_name) -%}
https://{{ public_hostname }}/{{ service_name }}/
{%- endmacro %}
