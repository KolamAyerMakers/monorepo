include:
  - nftables

{% set configured_port = salt['pillar.get']('openssh-server:config:Port', 22) %}
{% set ports = configured_port if configured_port is sequence and configured_port is not string else [configured_port] %}
{% set port_match = '{ ' ~ ports | join(', ') ~ ' }' if ports | length > 1 else ports[0] %}
{% set allowed_interfaces = salt['pillar.get']('openssh-server:firewall:allowed_interfaces', []) %}
{% set allowed_source_ipv4_prefixes = salt['pillar.get']('openssh-server:firewall:allowed_source_ipv4_prefixes', []) %}
{% set allowed_source_ipv6_prefixes = salt['pillar.get']('openssh-server:firewall:allowed_source_ipv6_prefixes', []) %}
{% set allowed_source_ipv4_prefixes_by_interface = salt['pillar.get']('openssh-server:firewall:allowed_source_ipv4_prefixes_by_interface', {}) %}

/etc/nftables.d/50-openssh-server.nft:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
        # OpenSSH server — allow inbound SSH connections
{% if allowed_interfaces or allowed_source_ipv4_prefixes or allowed_source_ipv6_prefixes or allowed_source_ipv4_prefixes_by_interface %}
        # Restricted to specific interfaces and/or source prefixes. Other traffic is blocked
        # at the firewall level (defense-in-depth alongside sshd's own
        # key-only auth and AllowUsers restrictions).
        table inet filter {
{% if allowed_source_ipv4_prefixes %}
            set openssh_server_allowed_ipv4_sources {
                type ipv4_addr
                flags interval
                elements = { {{ allowed_source_ipv4_prefixes | join(', ') }} }
            }

{% endif %}{# if allowed_source_ipv4_prefixes #}
{% for interface, source_prefixes in allowed_source_ipv4_prefixes_by_interface.items() if source_prefixes %}
            set openssh_server_allowed_ipv4_sources_{{ interface | replace('.', '_') | replace('-', '_') }} {
                type ipv4_addr
                flags interval
                elements = { {{ source_prefixes | join(', ') }} }
            }

{% endfor %}{# for interface, source_prefixes #}
{% if allowed_source_ipv6_prefixes %}
            set openssh_server_allowed_ipv6_sources {
                type ipv6_addr
                flags interval
                elements = { {{ allowed_source_ipv6_prefixes | join(', ') }} }
            }

{% endif %}{# if allowed_source_ipv6_prefixes #}
            counter input_ssh {}
{% if allowed_source_ipv4_prefixes %}
            counter input_ssh_ipv4_sources {}
{% endif %}{# if allowed_source_ipv4_prefixes #}
{% for interface, source_prefixes in allowed_source_ipv4_prefixes_by_interface.items() if source_prefixes %}
            counter input_ssh_ipv4_sources_{{ interface | replace('.', '_') | replace('-', '_') }} {}
{% endfor %}{# for interface, source_prefixes #}
{% if allowed_source_ipv6_prefixes %}
            counter input_ssh_ipv6_sources {}
{% endif %}{# if allowed_source_ipv6_prefixes #}
            chain input {
{% if allowed_interfaces %}
{% for interface in allowed_interfaces %}
{% if allowed_source_ipv4_prefixes %}
                iifname "{{ interface }}" \
                    ip saddr @openssh_server_allowed_ipv4_sources \
                    tcp dport {{ port_match }} \
                    counter name "input_ssh_ipv4_sources" accept \
                    comment "OpenSSH server"
{% endif %}{# if allowed_source_ipv4_prefixes #}
{% if allowed_source_ipv6_prefixes %}
                iifname "{{ interface }}" \
                    ip6 saddr @openssh_server_allowed_ipv6_sources \
                    tcp dport {{ port_match }} \
                    counter name "input_ssh_ipv6_sources" accept \
                    comment "OpenSSH server"
{% endif %}{# if allowed_source_ipv6_prefixes #}
{% if not allowed_source_ipv4_prefixes and not allowed_source_ipv6_prefixes %}
                iifname "{{ interface }}" tcp dport {{ port_match }} counter name "input_ssh" accept comment "OpenSSH server"
{% endif %}{# if not allowed sources #}
{% endfor %}{# for interface in allowed_interfaces #}
{% else %}{# if allowed_interfaces #}
{% if allowed_source_ipv4_prefixes %}
                ip saddr @openssh_server_allowed_ipv4_sources \
                    tcp dport {{ port_match }} \
                    counter name "input_ssh_ipv4_sources" accept \
                    comment "OpenSSH server"
{% endif %}{# if allowed_source_ipv4_prefixes #}
{% if allowed_source_ipv6_prefixes %}
                ip6 saddr @openssh_server_allowed_ipv6_sources \
                    tcp dport {{ port_match }} \
                    counter name "input_ssh_ipv6_sources" accept \
                    comment "OpenSSH server"
{% endif %}{# if allowed_source_ipv6_prefixes #}
{% endif %}{# if allowed_interfaces #}
{% for interface, source_prefixes in allowed_source_ipv4_prefixes_by_interface.items() if source_prefixes %}
                iifname "{{ interface }}" \
                    ip saddr @openssh_server_allowed_ipv4_sources_{{ interface | replace('.', '_') | replace('-', '_') }} \
                    tcp dport {{ port_match }} \
                    counter name "input_ssh_ipv4_sources_{{ interface | replace('.', '_') | replace('-', '_') }}" accept \
                    comment "OpenSSH server"
{% endfor %}{# for interface, source_prefixes #}
            }
        }
{% else %}
        # No OpenSSH firewall allowlist configured. Keep the chain empty so
        # nftables default policy decides exposure.
        table inet filter {
            counter input_ssh {}
            chain input {
            }
        }
{% endif %}
    - require:
      - file: /etc/nftables.d
    - watch_in:
      - cmd: nftables::validate
