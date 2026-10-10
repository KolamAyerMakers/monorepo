# Kam Classroom TODO

## Weather API egress

- Apply and rehearse the learner-group HTTPS allowlist for both Open-Meteo APIs;
  confirm DNS-populated IPv4/IPv6 sets before treating learner access as verified.

## Deployment Environment

-   Replace `grains.id == 'kam-classroom-dev'` checks with an explicit
  deployment environment signal.

-   The current host-name check is fragile and makes dev/prod behavior depend on
  a specific minion id.

-   Decide on a clean source of truth, such as `kam_classroom:environment`, and
  use it consistently in pillar and states.
