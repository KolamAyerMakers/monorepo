"""Pulumi entry point for the Kolam Ayer Makers Cloudflare Pages project."""

import pulumi
import pulumi_cloudflare as cloudflare

configuration = pulumi.Config()
account_id = configuration.require("cloudflareAccountId")
project_name = configuration.require("projectName")
custom_domain = configuration.get("customDomain") or "kolamayermakers.org"
project = cloudflare.PagesProject(
    "kolam-ayer-makers",
    account_id=account_id,
    name=project_name,
    production_branch=configuration.get("productionBranch") or "main",
    build_config={
        "build_command": "pnpm run build",
        "destination_dir": "dist",
        "root_dir": "website",
    },
    source={
        "type": "github",
        "config": {
            "owner": "KolamAyerMakers",
            "repo_name": "monorepo",
            "path_includes": ["website/*"],
            "preview_deployment_setting": "all",
            "production_deployments_enabled": True,
        },
    },
)
pages_domain = cloudflare.PagesDomain(
    "kolam-makers-domain",
    account_id=account_id,
    name=custom_domain,
    project_name=project_name,
    opts=pulumi.ResourceOptions(depends_on=[project]),
)
cloudflare_zone = cloudflare.get_zone(
    filter={
        "account": {"id": account_id},
        "match": "all",
        "name": custom_domain,
    }
)
cloudflare.DnsRecord(
    "kolam-makers-pages-dns-record",
    zone_id=cloudflare_zone.zone_id,
    name=custom_domain,
    type="CNAME",
    content=project.subdomain,
    proxied=True,
    ttl=1.0,
    opts=pulumi.ResourceOptions(depends_on=[pages_domain]),
)

pulumi.export(
    "pages_url", project.subdomain.apply(lambda subdomain: f"https://{subdomain}")
)
