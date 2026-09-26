# Add a health page

Quest: add-health-page

## Mission

Publish a small page you can request to check that your server serves files.

## Create And Publish

Open `micro ~/src/pages/health.md` and add:

```markdown
# Health

The web server can serve this page.
```

Save, exit, and publish:

```bash
build-website
curl -i "https://$USER.lf2607.kolamayermakers.org/health.html"
```

Check the status and page text. This tests one file request, not every part of your website. Keep editing the source under `~/src/pages`, not the generated HTML.

## Related Reading

- [build-website](../commands/build-website.md)
- [curl](../commands/curl.md)
- [multi-page sites](../concepts/multi-page-sites.md)
- [HTTP](../concepts/http.md)
