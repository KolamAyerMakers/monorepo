/etc/apt/sources.list:
  file.managed:
    - contents: ''
    - user: root
    - group: root
    - mode: '0644'
    - watch_in:
      - module: apt::refresh

# Legacy cleanup for previously managed sources
/etc/apt/sources.list.d/google-chrome.list.distUpgrade:
  file.absent:
    - watch_in:
      - module: apt::refresh

/etc/apt/sources.list.d/system76.sources:
  file.absent:
    - watch_in:
      - module: apt::refresh

/etc/apt/sources.list.d/system76.sources.save:
  file.absent:
    - watch_in:
      - module: apt::refresh

/etc/apt/keyrings/system76.gpg:
  file.absent:
    - watch_in:
      - module: apt::refresh

{% for name in salt['pillar.get']('apt:keys', {}) %}
/etc/apt/keyrings/{{ name }}.gpg:
  file.decode:
    - contents_pillar: apt:keys:{{ name }}
    - watch_in:
      - module: apt::refresh
{% endfor %}

{% for name, key in salt['pillar.get']('apt:key_urls', {}).items() %}
/etc/apt/keyrings/{{ name }}.asc:
  file.managed:
    - source: {{ key.source }}
    - source_hash: {{ key.source_hash }}
    - user: root
    - group: root
    - mode: '0644'
    - watch_in:
      - module: apt::refresh
{% endfor %}

{% set sources = salt['pillar.get']('apt:sources', {}) %}
{% set source_keys = salt['pillar.get']('apt:source_keys', {}) %}
{% set ubuntu_sources = {} %}
{% set debian_sources = {} %}
{% set custom_sources = {} %}

{# Group distro-prefixed sources into consolidated files #}
{% for name, data in sources.items() %}
{%   if name.startswith('ubuntu-') %}
{%     do ubuntu_sources.update({name: data}) %}
{%   elif name.startswith('debian-') %}
{%     do debian_sources.update({name: data}) %}
{%   else %}
{%     do custom_sources.update({name: data}) %}
{%   endif %}
{% endfor %}

{% for name in sources.keys() %}
/etc/apt/sources.list.d/{{ name }}.list:
  file.absent:
    - watch_in:
      - module: apt::refresh
{% endfor %}

{% if ubuntu_sources %}
/etc/apt/sources.list.d/ubuntu.sources:
  file.managed:
    - contents: |
{{ salt['apt.render_sources'](ubuntu_sources, source_keys) | indent(8, true) }}
    - watch_in:
      - module: apt::refresh
{% endif %}

{% if debian_sources %}
/etc/apt/sources.list.d/debian.sources:
  file.managed:
    - contents: |
{{ salt['apt.render_sources'](debian_sources, source_keys) | indent(8, true) }}
    - watch_in:
      - module: apt::refresh
{% endif %}

{% for name, config in custom_sources.items() %}
/etc/apt/sources.list.d/{{ name }}.sources:
  file.managed:
    - contents: |
{{ salt['apt.render_sources']({name: config}, source_keys) | indent(8, true) }}
    - watch_in:
      - module: apt::refresh
{% endfor %}
