include:
  - forgejo.service

{% set forgejo = salt['pillar.get']('forgejo', {}) %}
{% set paths = forgejo.get('paths', {}) %}
{% set service = forgejo.get('service', {}) %}
{% set oauth_sources = forgejo.get('oauth_sources', {}) %}

{% for name, source in oauth_sources.items() %}
{%   set group_claim_flag = '' %}
{%   if source.get('group_claim_name') %}
{%     set group_claim_flag = ' --group-claim-name ' ~ source.group_claim_name %}
{%   endif %}{# if source.get('group_claim_name') #}
{%   set skip_local_2fa_flag = '' %}
{%   if source.get('skip_local_2fa') %}
{%     set skip_local_2fa_flag = ' --skip-local-2fa' %}
{%   endif %}{# if source.get('skip_local_2fa') #}
{%   set sync_command = '/usr/local/sbin/forgejo-sync-oauth-source'
      ~ ' --name ' ~ name
      ~ ' --provider ' ~ source.provider
      ~ ' --client-id ' ~ source.client_id
      ~ ' --client-secret-file ' ~ source.client_secret_file
      ~ ' --auto-discover-url ' ~ source.auto_discover_url
      ~ ' --scope "' ~ source.scopes | join(' ') ~ '"'
      ~ group_claim_flag
      ~ skip_local_2fa_flag %}
forgejo::oauth_source::{{ name }}::required_pillar:
  test.check_pillar:
    - string:
      - forgejo:oauth_sources:{{ name }}:provider
      - forgejo:oauth_sources:{{ name }}:client_id
      - forgejo:oauth_sources:{{ name }}:client_secret
      - forgejo:oauth_sources:{{ name }}:client_secret_file
      - forgejo:oauth_sources:{{ name }}:auto_discover_url
    - listing:
      - forgejo:oauth_sources:{{ name }}:scopes
    - failhard: true

forgejo::oauth_source::{{ name }}::client_secret_file:
  file.managed:
    - name: {{ source.client_secret_file }}
    - user: root
    - group: {{ service.group }}
    - mode: '0640'
    - contents: |
        {{ source.client_secret | trim }}
    - require:
      - file: forgejo::secret_directory
      - test: forgejo::oauth_source::{{ name }}::required_pillar

/usr/local/sbin/forgejo-sync-oauth-source:
  file.managed:
    - source: salt://forgejo/files/forgejo_sync_oauth_source.py
    - user: root
    - group: root
    - mode: '0755'

forgejo::oauth_source::{{ name }}::discovery_available:
  cmd.run:
    - name: |
        /usr/bin/python3 <<'PYTHON'
        import time
        import urllib.request

        url = {{ source.auto_discover_url | tojson }}
        deadline = time.monotonic() + 180
        while True:
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    if 200 <= response.status < 300:
                        break
            except Exception:
                pass
            if time.monotonic() >= deadline:
                raise SystemExit(f"Timed out waiting for {url}")
            time.sleep(5)
        PYTHON
    - unless: |
        /usr/bin/python3 <<'PYTHON'
        import urllib.request

        with urllib.request.urlopen({{ source.auto_discover_url | tojson }}, timeout=5) as response:
            raise SystemExit(0 if 200 <= response.status < 300 else 1)
        PYTHON
    - require:
      - service: forgejo::service
      - test: forgejo::oauth_source::{{ name }}::required_pillar
{% for requisite in source.get('require', []) %}
{%   for requisite_type, requisite_identifier in requisite.items() %}
      - {{ requisite_type }}: {{ requisite_identifier }}
{%   endfor %}{# for requisite_type, requisite_identifier in requisite.items() #}
{% endfor %}{# for requisite in source.get('require', []) #}

forgejo::oauth_source::{{ name }}:
  cmd.run:
    - name: {{ sync_command }}
    - runas: {{ service.user }}
    - unless: >-
        {{ sync_command }} --check
    - require:
      - service: forgejo::service
      - cmd: forgejo::oauth_source::{{ name }}::discovery_available
      - file: /usr/local/sbin/forgejo-sync-oauth-source
      - file: forgejo::oauth_source::{{ name }}::client_secret_file
      - test: forgejo::oauth_source::{{ name }}::required_pillar
{% for requisite in source.get('require', []) %}
{%   for requisite_type, requisite_identifier in requisite.items() %}
      - {{ requisite_type }}: {{ requisite_identifier }}
{%   endfor %}{# for requisite_type, requisite_identifier in requisite.items() #}
{% endfor %}{# for requisite in source.get('require', []) #}

forgejo::oauth_source::{{ name }}::updated:
  cmd.run:
    - name: {{ sync_command }}
    - runas: {{ service.user }}
    - onchanges:
      - file: forgejo::oauth_source::{{ name }}::client_secret_file
      - file: /usr/local/sbin/forgejo-sync-oauth-source
    - require:
      - cmd: forgejo::oauth_source::{{ name }}
      - file: /usr/local/sbin/forgejo-sync-oauth-source
      - file: forgejo::oauth_source::{{ name }}::client_secret_file
      - test: forgejo::oauth_source::{{ name }}::required_pillar
{% for requisite in source.get('require', []) %}
{%   for requisite_type, requisite_identifier in requisite.items() %}
      - {{ requisite_type }}: {{ requisite_identifier }}
{%   endfor %}{# for requisite_type, requisite_identifier in requisite.items() #}
{% endfor %}{# for requisite in source.get('require', []) #}

{% endfor %}
