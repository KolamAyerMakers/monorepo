{% from "bootstrap/macros/packages.sls" import bootstrap_package_installed %}

include:
  - github.download_egress
  - nodejs.package

{{ bootstrap_package_installed('patch', state_identifier='gamja::patch') }}

{% set gamja = salt['pillar.get']('gamja', {}) %}
{% set version = gamja.get('version', '') %}
{% set source = gamja.get('source', {}) %}
{% set paths = gamja.get('paths', {}) %}
{% set version_directory = paths.get('package_directory', '') ~ '/' ~ version %}
{% set source_directory = version_directory ~ '/source' %}
{% set install_directory = version_directory ~ '/install' %}

gamja::package::required_pillar:
  test.check_pillar:
    - string:
      - gamja:version
      - gamja:source:url
      - gamja:source:checksum
      - gamja:paths:package_directory
      - gamja:paths:web_root
    - failhard: true

{{ paths.package_directory }}:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - makedirs: true
    - require:
      - test: gamja::package::required_pillar

gamja::source:
  archive.extracted:
    - name: {{ source_directory }}
    - source: {{ source.url.format(version=version) }}
    - source_hash: {{ source.checksum }}
    - enforce_toplevel: false
    - force: true
    - keep_source: false
    - options: --strip-components=1
    - if_missing: {{ source_directory }}/package.json
    - require:
      - file: {{ paths.package_directory }}
      - test: gamja::package::required_pillar

# Adds PKCE support so Gamja can authenticate against Authelia's OIDC provider.
gamja::oauth2_pkce_patch_file:
  file.managed:
    - name: {{ source_directory }}/km-oauth2-pkce.patch
    - source: salt://gamja/files/oauth2_pkce.patch
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - archive: gamja::source
      - test: gamja::package::required_pillar

# Makes the OAuth callback pass the returned state into the token exchange.
gamja::oauth2_pkce_state_callback_patch_file:
  file.managed:
    - name: {{ source_directory }}/km-oauth2-pkce-state-callback.patch
    - source: salt://gamja/files/oauth2_pkce_state_callback.patch
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - archive: gamja::source
      - test: gamja::package::required_pillar

# Removes Authelia callback parameters from the redirect URI used for token exchange.
gamja::oauth2_redirect_uri_cleanup_patch_file:
  file.managed:
    - name: {{ source_directory }}/km-oauth2-redirect-uri-cleanup.patch
    - source: salt://gamja/files/oauth2_redirect_uri_cleanup.patch
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - archive: gamja::source
      - test: gamja::package::required_pillar

# Sends the public OAuth client_id when introspecting a bearer token without a client secret.
gamja::oauth2_introspection_client_id_patch_file:
  file.managed:
    - name: {{ source_directory }}/km-oauth2-introspection-client-id.patch
    - source: salt://gamja/files/oauth2_introspection_client_id.patch
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - archive: gamja::source
      - test: gamja::package::required_pillar

# Renames the introspection request body variable after earlier patch iterations.
gamja::oauth2_introspection_client_id_binding_repair_patch_file:
  file.managed:
    - name: {{ source_directory }}/km-oauth2-introspection-client-id-binding-repair.patch
    - source: salt://gamja/files/oauth2_introspection_client_id_binding_repair.patch
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - archive: gamja::source
      - test: gamja::package::required_pillar

# Uses the authenticated OAuth username as Gamja's nick, username, and realname.
gamja::oauth2_account_identity_patch_file:
  file.managed:
    - name: {{ source_directory }}/km-oauth2-account-identity.patch
    - source: salt://gamja/files/oauth2_account_identity.patch
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - archive: gamja::source
      - test: gamja::package::required_pillar

gamja::oauth2_pkce_patch:
  cmd.run:
    - name: patch -p1 --forward --input {{ source_directory }}/km-oauth2-pkce.patch
    - cwd: {{ source_directory }}
    - unless: grep -Fq "code_challenge_method" {{ source_directory }}/lib/oauth2.js
    - require:
      - pkg: gamja::patch
      - file: gamja::oauth2_pkce_patch_file
      - test: gamja::package::required_pillar

gamja::oauth2_pkce_state_callback_patch:
  cmd.run:
    - name: patch -p1 --forward --input {{ source_directory }}/km-oauth2-pkce-state-callback.patch
    - cwd: {{ source_directory }}
    - onlyif: grep -Fq "code_challenge_method" {{ source_directory }}/lib/oauth2.js
    - unless: grep -Fq "exchangeOauth2Code(queryParams.code, queryParams.state)" {{ source_directory }}/components/app.js
    - require:
      - pkg: gamja::patch
      - file: gamja::oauth2_pkce_state_callback_patch_file
      - cmd: gamja::oauth2_pkce_patch
      - test: gamja::package::required_pillar

gamja::oauth2_redirect_uri_cleanup_patch:
  cmd.run:
    - name: patch -p1 --forward --input {{ source_directory }}/km-oauth2-redirect-uri-cleanup.patch
    - cwd: {{ source_directory }}
    - onlyif: grep -Fq "code_challenge_method" {{ source_directory }}/lib/oauth2.js
    - unless: grep -Fq 'redirectUri.searchParams.delete("iss")' {{ source_directory }}/components/app.js
    - require:
      - pkg: gamja::patch
      - file: gamja::oauth2_redirect_uri_cleanup_patch_file
      - cmd: gamja::oauth2_pkce_state_callback_patch
      - test: gamja::package::required_pillar

gamja::oauth2_introspection_client_id_patch:
  cmd.run:
    - name: patch -p1 --forward --input {{ source_directory }}/km-oauth2-introspection-client-id.patch
    - cwd: {{ source_directory }}
    - onlyif: grep -Fq "code_challenge_method" {{ source_directory }}/lib/oauth2.js
    - unless: grep -Fq 'requestData["client_id"] = clientId' {{ source_directory }}/lib/oauth2.js
    - require:
      - pkg: gamja::patch
      - file: gamja::oauth2_introspection_client_id_patch_file
      - cmd: gamja::oauth2_introspection_client_id_binding_repair_patch
      - test: gamja::package::required_pillar

gamja::oauth2_introspection_client_id_binding_repair_patch:
  cmd.run:
    - name: patch -p1 --forward --input {{ source_directory }}/km-oauth2-introspection-client-id-binding-repair.patch
    - cwd: {{ source_directory }}
    - onlyif: grep -Fq 'let data = { token };' {{ source_directory }}/lib/oauth2.js
    - unless: grep -Fq 'let requestData = { token };' {{ source_directory }}/lib/oauth2.js
    - require:
      - pkg: gamja::patch
      - file: gamja::oauth2_introspection_client_id_binding_repair_patch_file
      - cmd: gamja::oauth2_redirect_uri_cleanup_patch
      - test: gamja::package::required_pillar

gamja::oauth2_account_identity_patch:
  cmd.run:
    - name: patch -p1 --forward --input {{ source_directory }}/km-oauth2-account-identity.patch
    - cwd: {{ source_directory }}
    - onlyif: grep -Fq 'connectParams.saslOauthBearer = saslOauthBearer' {{ source_directory }}/components/app.js
    - unless: grep -Fq 'connectParams.realname = saslOauthBearer.username' {{ source_directory }}/components/app.js
    - require:
      - pkg: gamja::patch
      - file: gamja::oauth2_account_identity_patch_file
      - cmd: gamja::oauth2_introspection_client_id_patch
      - test: gamja::package::required_pillar

gamja::build:
  cmd.run:
    - name: >-
        /bin/bash -lc 'export PATH="/opt/packages/nodejs/bin:$PATH" &&
        npm ci --include=dev &&
        rm -rf dist &&
        npm run build &&
        rm -rf {{ install_directory }} &&
        install -d -m 0755 {{ install_directory }} &&
        cp -a dist/. {{ install_directory }}/ &&
        printf "%s\n" oauth2-account-identity-v1 > {{ install_directory }}/.km-build-id'
    - cwd: {{ source_directory }}
    - unless: grep -Fxq oauth2-account-identity-v1 {{ install_directory }}/.km-build-id
    - require:
      - cmd: gamja::oauth2_account_identity_patch
      - packages: nodejs::package
      - test: gamja::package::required_pillar

{{ paths.web_root }}:
  file.symlink:
    - target: {{ install_directory }}
    - force: true
    - makedirs: true
    - require:
      - cmd: gamja::build
      - test: gamja::package::required_pillar
