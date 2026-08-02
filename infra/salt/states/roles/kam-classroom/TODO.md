# Kam Classroom TODO

## Deployment Environment

-   Replace `grains.id == 'kam-classroom-dev'` checks with an explicit
  deployment environment signal.

-   The current host-name check is fragile and makes dev/prod behavior depend on
  a specific minion id.

-   Decide on a clean source of truth, such as `kam_classroom:environment`, and
  use it consistently in pillar and states.
