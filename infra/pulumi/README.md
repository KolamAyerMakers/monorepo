# Pulumi Operations

The projects use the Pulumi Service backend at `https://api.pulumi.com` under the `pmuller` account. The `classroom` project uses the `development` and `production-lf2607` stacks. The `kam-website` project uses the `production` stack. Their committed `Pulumi.*.yaml` files contain encrypted configuration and must remain tracked.

The selected secrets provider is the Pulumi Service provider. Recovery owners and cloud-account recovery contacts are recorded in the private operational access register, not this public repository. A recovery owner restores Pulumi Service access first, then verifies the stack secrets provider with `pulumi stack export --show-secrets=false` before rotating affected Cloudflare or UpCloud tokens with `pulumi config set --secret`.

Use `pulumi preview` for review. Only an authorized operator may run `pulumi up`; CI never runs it.
