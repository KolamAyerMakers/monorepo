{% set public_hostname = salt['pillar.get']('kam_classroom:domain:public_hostname') %}

roles::kam_classroom::hosts::required_pillar:
  test.check_pillar:
    - string:
      - kam_classroom:domain:public_hostname
    - failhard: true

roles::kam_classroom::hosts::service_domains:
  host.present:
    - ip: 127.0.0.1
    - names:
      - {{ public_hostname }}
    - require:
      - test: roles::kam_classroom::hosts::required_pillar
