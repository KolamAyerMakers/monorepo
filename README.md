# Kolam Ayer Makers

Kolam Ayer Makers is a neighborhood maker group at Kolam Ayer Community Club in Singapore.

This repository contains the Maker Guide learner-support application, public website, brand assets, Pulumi infrastructure definitions, and the Salt configuration for the classroom server.

## Layout

- `maker-guide/`: learner support and teaching automation.
- `website/`: public Astro website.
- `branding/`: source brand assets and usage guide.
- `infra/pulumi/`: explicit cloud infrastructure changes.
- `infra/salt/`: classroom server configuration and deployment tooling.
- `infra/ops/`: manual classroom recovery tooling.

## Development

Install Git hooks with `uv run lefthook install`. Each subproject documents its own commands. Infrastructure changes are manual operator actions; CI never applies Pulumi or Salt.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
