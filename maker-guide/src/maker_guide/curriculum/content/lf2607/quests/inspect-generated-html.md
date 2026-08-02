# Inspect generated HTML

Quest: inspect-generated-html

## Mission

Inspect `~/public_html/setup.html` and find generated HTML tags.

## Commands You Will Use

- `cat`
- `grep`

## Steps

1. Open or print `~/public_html/setup.html`.
2. Search for generated tags such as `<h1>`.
3. Confirm the page contains your setup content.
4. Ask the guide to check the generated file.

## Hints

1. Source Markdown becomes generated HTML.
2. `grep` can search for tags or words.
3. Rebuild if the generated file is missing.

## If Check Fails

Run `build-website` and inspect `~/public_html/setup.html` again.

## Related Reading

- [cat](../commands/cat.md)
- [grep](../commands/grep.md)
- [HTML on the wire](../concepts/html-on-the-wire.md)
- [first site build](../concepts/first-site-build.md)
