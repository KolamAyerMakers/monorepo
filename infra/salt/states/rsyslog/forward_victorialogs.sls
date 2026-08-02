{% from "bootstrap/macros/packages.sls" import bootstrap_package_installed %}
{% set rsyslog = salt['pillar.get']('rsyslog', {}) %}
{% set service = rsyslog.get('service', {}) %}
{% set forwarding = rsyslog.get('victorialogs_forward', {}) %}
{% set receiver = rsyslog.get('receiver', {}) %}
{% set imjournal = forwarding.get('imjournal', {}) %}
{% set queue = forwarding.get('queue', {}) %}

{% if forwarding.get('enabled') is sameas true %}
include:
  - bootstrap.packages

{{ bootstrap_package_installed('rsyslog', 'rsyslog::package') }}

rsyslog::victorialogs_forward::required_pillar:
  test.check_pillar:
    - string:
      - rsyslog:service:name
      - rsyslog:service:main_configuration_file
      - rsyslog:service:local_default_configuration_file
      - rsyslog:service:configuration_file
      - rsyslog:service:queue_spool_directory
      - rsyslog:service:queue_spool_user
      - rsyslog:service:queue_spool_group
      - rsyslog:service:log_file_owner
      - rsyslog:service:log_file_group
      - rsyslog:service:log_file_create_mode
      - rsyslog:service:log_directory_create_mode
      - rsyslog:service:umask
      - rsyslog:victorialogs_forward:target
      - rsyslog:victorialogs_forward:protocol
      - rsyslog:victorialogs_forward:template
      - rsyslog:victorialogs_forward:local_hostname
      - rsyslog:victorialogs_forward:source_name_map_file
      - rsyslog:victorialogs_forward:imjournal:state_file
      - rsyslog:victorialogs_forward:imjournal:file_create_mode
      - rsyslog:victorialogs_forward:queue:type
      - rsyslog:victorialogs_forward:queue:filename
      - rsyslog:victorialogs_forward:queue:max_disk_space
    - integer:
      - rsyslog:victorialogs_forward:port
      - rsyslog:receiver:tcp_listen_port
      - rsyslog:receiver:udp_listen_port
      - rsyslog:victorialogs_forward:imjournal:persist_state_interval
      - rsyslog:victorialogs_forward:queue:size
      - rsyslog:victorialogs_forward:queue:high_watermark
      - rsyslog:victorialogs_forward:queue:low_watermark
    - boolean:
      - rsyslog:victorialogs_forward:enabled
      - rsyslog:receiver:enabled
      - rsyslog:victorialogs_forward:imjournal:ignore_previous_messages
      - rsyslog:victorialogs_forward:queue:save_on_shutdown
    - dictionary:
      - rsyslog:receiver:source_name_map
    - failhard: true

{{ service.queue_spool_directory }}:
  file.directory:
    - user: {{ service.queue_spool_user }}
    - group: {{ service.queue_spool_group }}
    - mode: '0750'
    - makedirs: true
    - require:
      - pkg: rsyslog::package
      - test: rsyslog::victorialogs_forward::required_pillar

rsyslog::victorialogs_forward::legacy_state_directory:
  file.absent:
    - name: {{ service.queue_spool_directory }}/{{ imjournal.state_file }}
    - onlyif: test -d {{ service.queue_spool_directory }}/{{ imjournal.state_file }}
    - require:
      - file: {{ service.queue_spool_directory }}
      - test: rsyslog::victorialogs_forward::required_pillar

rsyslog::main_configuration:
  file.managed:
    - name: {{ service.main_configuration_file }}
    - source: salt://rsyslog/rsyslog.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        service: {{ service | yaml }}
        forwarding: {{ forwarding | yaml }}
        receiver: {{ receiver | yaml }}
        imjournal: {{ imjournal | yaml }}
    - require:
      - pkg: rsyslog::package
      - file: {{ service.queue_spool_directory }}
      - file: rsyslog::victorialogs_forward::legacy_state_directory
      - test: rsyslog::victorialogs_forward::required_pillar

rsyslog::local_default_configuration:
  file.managed:
    - name: {{ service.local_default_configuration_file }}
    - source: salt://rsyslog/50-default.conf
    - user: root
    - group: root
    - mode: '0644'
    - unless: test -e {{ service.local_default_configuration_file }}
    - require:
      - pkg: rsyslog::package
      - file: rsyslog::main_configuration
      - test: rsyslog::victorialogs_forward::required_pillar

rsyslog::victorialogs_forward::source_name_map:
  file.managed:
    - name: {{ forwarding.source_name_map_file }}
    - source: salt://rsyslog/syslog-source-names.json.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        source_name_map: {{ receiver.source_name_map | yaml }}
    - require:
      - pkg: rsyslog::package
      - test: rsyslog::victorialogs_forward::required_pillar

rsyslog::victorialogs_forward::configuration:
  file.managed:
    - name: {{ service.configuration_file }}
    - source: salt://rsyslog/victorialogs-forward.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        service: {{ service | yaml }}
        forwarding: {{ forwarding | yaml }}
        receiver: {{ receiver | yaml }}
        queue: {{ queue | yaml }}
    - require:
      - pkg: rsyslog::package
      - file: rsyslog::main_configuration
      - file: rsyslog::local_default_configuration
      - file: rsyslog::victorialogs_forward::source_name_map
      - test: rsyslog::victorialogs_forward::required_pillar

rsyslog::service:
  service.running:
    - name: {{ service.name }}
    - enable: true
    - require:
      - pkg: rsyslog::package
      - file: rsyslog::main_configuration
      - file: rsyslog::local_default_configuration
      - file: rsyslog::victorialogs_forward::source_name_map
      - file: rsyslog::victorialogs_forward::configuration
      - test: rsyslog::victorialogs_forward::required_pillar
    - watch:
      - file: rsyslog::main_configuration
      - file: rsyslog::local_default_configuration
      - file: rsyslog::victorialogs_forward::source_name_map
      - file: rsyslog::victorialogs_forward::configuration
{% else %}
rsyslog::victorialogs_forward::disabled:
  test.nop:
    - name: rsyslog::victorialogs_forward::disabled
{% endif %}
