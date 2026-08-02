{% set npm_global_packages = salt['pillar.get']('packages:nodejs:npm_global_packages', {}) %}
{% set enabled_npm_global_package_names = salt['pillar.get']('packages:nodejs:enabled_npm_global_packages', npm_global_packages.keys()) %}
{% set node_package_directory = '/opt/packages/nodejs' %}
{% set node_version = salt['pillar.get']('packages:nodejs:version') %}
{% set users = salt['pillar.get']('users', {}) %}

{% for package_name in enabled_npm_global_package_names %}
{%   set package_configuration = npm_global_packages[package_name] %}
{%   set sanitized_package_name = package_name.replace('@', '').replace('/', '-') %}
{%   set package_version = package_configuration['version'] %}
{%   set binaries = package_configuration.get('managed_binaries', package_configuration.get('binaries', [])) %}
{%   set package_json = node_package_directory ~ '/lib/node_modules/' ~ package_name ~ '/package.json' %}
{%   set version_check = "try{console.log(require('" ~ package_json ~ "').version)}catch(error){process.exit(1)}" %}

nodejs::npm_global::{{ sanitized_package_name }}::install:
  cmd.run:
    - name: npm install -g "{{ package_name }}@{{ package_version }}"
    - unless: test "$(node -e "{{ version_check }}")" = "{{ package_version }}"
    - require:
      - packages: nodejs::package

{%   for binary in binaries %}
nodejs::npm_global::{{ sanitized_package_name }}::{{ binary }}:
  file.symlink:
    - name: /usr/local/bin/{{ binary }}
    - target: {{ node_package_directory }}/bin/{{ binary }}
    - force: true
    - require:
      - cmd: nodejs::npm_global::{{ sanitized_package_name }}::install

{%     for username, user_configuration in users.items() if user_configuration is mapping and user_configuration.get('deploy', False) %}
{%       set home = salt['userpaths.get_home'](username) %}
nodejs::npm_global::{{ sanitized_package_name }}::{{ username }}::fnm_shadow::{{ binary }}:
  file.absent:
    - name: {{ home }}/.local/share/fnm/node-versions/v{{ node_version }}/installation/bin/{{ binary }}
    - require:
      - file: nodejs::npm_global::{{ sanitized_package_name }}::{{ binary }}
{%     endfor %}{# users #}
{%   endfor %}

{% endfor %}{# package_name #}
