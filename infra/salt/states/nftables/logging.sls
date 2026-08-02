{% set default_policies = salt['pillar.get']('nftables:default_policies', {}) %}
{% set input_policy = default_policies.get('input', 'drop') %}
{% set forward_policy = default_policies.get('forward', 'drop') %}
{% set output_policy = default_policies.get('output', 'drop') %}

include:
  - nftables

/etc/nftables.d/99-default-input-log.nft:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
        # Default drop logging — appended after all per-service accept rules.
        # Base chains remain policy drop; these rules add visibility for
        # unmatched traffic without shadowing earlier accept rules.
        table inet filter {
{% if input_policy == 'drop' %}
            counter input_default_log {}
            counter input_default_drop {}
{% endif %}{# if input_policy drop #}
{% if forward_policy == 'drop' %}
            counter fwd_policy_default_log {}
            counter fwd_policy_default_drop {}
{% endif %}{# if forward_policy drop #}
{% if output_policy == 'drop' %}
            counter output_default_log {}
            counter output_default_drop {}
{% endif %}{# if output_policy drop #}

{% if input_policy == 'drop' %}
            chain input {
                limit rate 10/second counter name "input_default_log" log prefix "nft-input-drop: "
                counter name "input_default_drop" drop
            }
{% endif %}{# if input_policy drop #}
{% if forward_policy == 'drop' %}
            chain forward {
                limit rate 10/second counter name "fwd_policy_default_log" log prefix "nft-forward-drop: "
                counter name "fwd_policy_default_drop" drop
            }
{% endif %}{# if forward_policy drop #}
{% if output_policy == 'drop' %}
            chain output {
                limit rate 10/second counter name "output_default_log" log prefix "nft-output-drop: "
                counter name "output_default_drop" drop
            }
{% endif %}{# if output_policy drop #}
        }
    - require:
      - file: /etc/nftables.d
    - watch_in:
      - cmd: nftables::validate
