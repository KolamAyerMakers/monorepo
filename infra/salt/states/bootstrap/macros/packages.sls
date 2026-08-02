{#
Bootstrap package macros.

These helpers emit the repetitive package states that participate in the
bootstrap staging graph.

Arguments:
- package_name: package/provider name passed to Salt
- pillar_key: pillar key used to read the package/provider name; when set, the
  macro emits a `test.check_pillar` guard with `failhard: true`
- state_identifier: optional Salt state ID override; leave unset unless another
  state already requires a non-default ID
- parameters: additional low-state arguments; prefer mappings, raw strings are
  still supported for backward compatibility
- extra_requirements: additional raw requisites appended under require

Common behavior:
- state ID defaults to package_name for readability
- apt-backed packages always require apt::refresh and
  bootstrap::package_sources_ready
- apt-backed packages also feed bootstrap::apt_packages_ready so firewall
  enforcement can wait until package installation is no longer dependent on the
  provider resolver path
- binary packages always require bootstrap::package_sources_ready and
  github::download_egress::ready

These macros are intentionally bootstrap-scoped. Do not use them for package
states that must remain independent from the bootstrap staging barriers.
#}
{% macro render_list_argument(parameter, indent_width=4) -%}
{% if parameter is mapping -%}
{% for key, value in parameter.items() -%}
{% if value is mapping or (value is sequence and value is not string) -%}
{{ ' ' * indent_width }}- {{ key }}:
{{ value|yaml(False)|indent(indent_width + 2, true) }}
{% elif value is sameas true -%}
{{ ' ' * indent_width }}- {{ key }}: true
{% elif value is sameas false -%}
{{ ' ' * indent_width }}- {{ key }}: false
{% elif value is none -%}
{{ ' ' * indent_width }}- {{ key }}: null
{% else -%}
{{ ' ' * indent_width }}- {{ key }}: {{ value|tojson }}
{% endif -%}
{% endfor -%}
{% else -%}
{{ ' ' * indent_width }}- {{ parameter }}
{% endif -%}
{%- endmacro %}

{% macro bootstrap_package_installed(package_name=None, state_identifier=None, parameters=None, extra_requirements=None, pillar_key=None) -%}
{% set resolved_package_name = salt['pillar.get'](pillar_key) if pillar_key else package_name %}
{% set resolved_state_identifier = state_identifier or resolved_package_name or pillar_key %}
{% set required_pillar_identifier = resolved_state_identifier ~ '::required_pillar' %}
{% if pillar_key %}
{{ required_pillar_identifier }}:
  test.check_pillar:
    - string:
      - {{ pillar_key }}
    - failhard: true

{% endif %}
{{ resolved_state_identifier }}:
  pkg.installed:
    - name: {{ resolved_package_name }}
{% for parameter in parameters or [] %}
{{ render_list_argument(parameter) -}}
{% endfor %}
    - require:
      - module: apt::refresh
      - test: bootstrap::package_sources_ready
{% if pillar_key %}
      - test: {{ required_pillar_identifier }}
{% endif %}
{% for requirement in extra_requirements or [] %}
{{ render_list_argument(requirement, indent_width=6) -}}
{% endfor %}
    - require_in:
      - test: bootstrap::apt_packages_ready
{%- endmacro %}

{#
Emit a packages.binary_package state that is gated on bootstrap package-source
readiness. Use this for downloaded binary artifacts that should not start until
bootstrap DNS/network/package-source prerequisites are in place.
#}
{% macro bootstrap_binary_package(package_name, state_identifier=None, parameters=None, extra_requirements=None) -%}
{{ state_identifier or package_name }}:
  packages.binary_package:
    - name: {{ package_name }}
{% for parameter in parameters or [] %}
{{ render_list_argument(parameter) -}}
{% endfor %}
    - require:
      - test: bootstrap::package_sources_ready
      - test: github::download_egress::ready
{% for requirement in extra_requirements or [] %}
{{ render_list_argument(requirement, indent_width=6) -}}
{% endfor %}
{%- endmacro %}
