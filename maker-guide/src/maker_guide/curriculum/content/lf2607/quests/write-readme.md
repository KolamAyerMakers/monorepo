# Write your README

Quest: write-readme

## Mission

Write a useful `~/src/README.md`, commit it, and push it.

## Commands You Will Use

- `micro`
- `vim`
- `git add`
- `git commit`
- `git push`

## Steps

1. Open `~/src/README.md`, preserving useful existing content.
2. Add a Markdown title, site description, build command, and service notes. Include runnable commands such as `build-website` and `systemctl --user start site.service`, not only the words "build" or "run".
3. Commit the README.
4. Push to Forgejo.
5. Ask the guide to check the file.

## Hints

1. A README is for another human.
2. Explain how to rebuild and run the site.
3. Include the actual build and `systemctl --user` commands so another person can repeat them.

## If Check Fails

Add missing sections for what the site is and how to run it.

## Related Reading

- [readme-writing](../concepts/readme-writing.md)
- [forgejo-publishing](../concepts/forgejo-publishing.md)
